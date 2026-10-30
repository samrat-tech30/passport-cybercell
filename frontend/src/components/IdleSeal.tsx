import { useEffect, useRef } from "react";

/* The idle-state seal: a guilloché rosette (the engraved pattern on real passports), drawn in 3D with WebGPU.
   Shown only before the first run, unmounted (and the GPU device destroyed) as soon as a run starts.
   No WebGPU, or any init error → the same rosette drawn once on a 2D canvas. Reduced motion → one still frame. */

// WebGPU types aren't in this TypeScript lib set and we add no packages; keep the surface small and local.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Gpu = any;

const SIZE = 240; // css px

/** Two bands of phase-shifted waves around a circle. Returns line-list vertices: x, y, z, band. */
function rosette(): Float32Array {
  const bands = [
    { r: 0.86, a: 0.075, k: 22, n: 14, band: 0 },
    { r: 0.52, a: 0.09, k: 14, n: 10, band: 1 },
    { r: 0.24, a: 0.05, k: 9, n: 6, band: 0 },
  ];
  const STEPS = 540;
  const out: number[] = [];
  for (const b of bands) {
    for (let j = 0; j < b.n; j++) {
      const ph = (j / b.n) * Math.PI * 2;
      let prev: number[] | null = null;
      for (let i = 0; i <= STEPS; i++) {
        const t = (i / STEPS) * Math.PI * 2;
        const w = Math.sin(b.k * t + ph);
        const rr = b.r + b.a * w;
        const p = [rr * Math.cos(t), rr * Math.sin(t), 0.06 * Math.cos(b.k * t + ph), b.band];
        if (prev) out.push(...prev, ...p);
        prev = p;
      }
    }
  }
  return new Float32Array(out);
}

/** Same projection as the shader, for the 2D fallback (one still frame). */
function project(x: number, y: number, z: number, time: number): [number, number, number] {
  const rz = time * 0.05;
  const tx = 0.5 + 0.1 * Math.sin(time * 0.3);
  const ty = 0.22 * Math.sin(time * 0.21);
  let px = x * Math.cos(rz) - y * Math.sin(rz);
  let py = x * Math.sin(rz) + y * Math.cos(rz);
  let pz = z;
  [py, pz] = [py * Math.cos(tx) - pz * Math.sin(tx), py * Math.sin(tx) + pz * Math.cos(tx)];
  [px, pz] = [px * Math.cos(ty) + pz * Math.sin(ty), -px * Math.sin(ty) + pz * Math.cos(ty)];
  const s = 2.6 / (2.6 + pz);
  return [px * s * 0.92, py * s * 0.92, pz];
}

const WGSL = /* wgsl */ `
struct U { time: f32, pad0: f32, pad1: f32, pad2: f32, c0: vec4f, c1: vec4f };
@group(0) @binding(0) var<uniform> u: U;
struct O { @builtin(position) pos: vec4f, @location(0) col: vec4f };

@vertex fn vs(@location(0) v: vec4f) -> O {
  let rz = u.time * 0.05;
  let tx = 0.5 + 0.1 * sin(u.time * 0.3);
  let ty = 0.22 * sin(u.time * 0.21);
  var p = vec3f(v.x * cos(rz) - v.y * sin(rz), v.x * sin(rz) + v.y * cos(rz), v.z);
  p = vec3f(p.x, p.y * cos(tx) - p.z * sin(tx), p.y * sin(tx) + p.z * cos(tx));
  p = vec3f(p.x * cos(ty) + p.z * sin(ty), p.y, -p.x * sin(ty) + p.z * cos(ty));
  let s = 2.6 / (2.6 + p.z);
  var o: O;
  o.pos = vec4f(p.x * s * 0.92, p.y * s * 0.92, 0.5, 1.0);
  let base = select(u.c0, u.c1, v.w > 0.5);
  let a = base.a * clamp(0.75 - p.z * 0.6, 0.25, 1.0);
  o.col = vec4f(base.rgb * a, a);
  return o;
}

@fragment fn fs(i: O) -> @location(0) vec4f { return i.col; }
`;

/** Reads a token like --color-brand into 0..1 rgb. */
function tokenRgb(name: string): [number, number, number] {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim().replace("#", "");
  const n = parseInt(v.length === 3 ? v.split("").map((c) => c + c).join("") : v.slice(0, 6), 16);
  return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
}

function drawFallback(canvas: HTMLCanvasElement, verts: Float32Array) {
  const dpr = Math.min(2, devicePixelRatio || 1);
  canvas.width = SIZE * dpr;
  canvas.height = SIZE * dpr;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const cols = [tokenRgb("--color-fg-muted"), tokenRgb("--color-brand")];
  const half = (SIZE * dpr) / 2;
  ctx.lineWidth = dpr * 0.6;
  for (let i = 0; i < verts.length; i += 8) {
    const [ax, ay] = project(verts[i], verts[i + 1], verts[i + 2], 0);
    const [bx, by] = project(verts[i + 4], verts[i + 5], verts[i + 6], 0);
    const [r, g, b] = cols[verts[i + 3] > 0.5 ? 1 : 0];
    ctx.strokeStyle = `rgba(${Math.round(r * 255)}, ${Math.round(g * 255)}, ${Math.round(b * 255)}, 0.45)`;
    ctx.beginPath();
    ctx.moveTo(half + ax * half, half - ay * half);
    ctx.lineTo(half + bx * half, half - by * half);
    ctx.stroke();
  }
}

export function IdleSeal() {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const verts = rosette();
    const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
    const gpu: Gpu = (navigator as unknown as { gpu?: Gpu }).gpu;
    let cancelled = false;
    let raf = 0;
    let device: Gpu = null;

    async function init() {
      if (!gpu) throw new Error("no webgpu");
      const adapter = await gpu.requestAdapter();
      if (!adapter) throw new Error("no adapter");
      device = await adapter.requestDevice();
      if (cancelled || !canvas) {
        device.destroy();
        return;
      }
      const dpr = Math.min(2, devicePixelRatio || 1);
      canvas.width = SIZE * dpr;
      canvas.height = SIZE * dpr;
      const ctx: Gpu = canvas.getContext("webgpu");
      if (!ctx) throw new Error("no context");
      const format = gpu.getPreferredCanvasFormat();
      ctx.configure({ device, format, alphaMode: "premultiplied" });

      const vbuf = device.createBuffer({ size: verts.byteLength, usage: 0x20 | 0x8 }); // VERTEX | COPY_DST
      device.queue.writeBuffer(vbuf, 0, verts);
      const ubuf = device.createBuffer({ size: 48, usage: 0x40 | 0x8 }); // UNIFORM | COPY_DST
      const module = device.createShaderModule({ code: WGSL });
      const pipeline = device.createRenderPipeline({
        layout: "auto",
        vertex: { module, entryPoint: "vs", buffers: [{ arrayStride: 16, attributes: [{ shaderLocation: 0, offset: 0, format: "float32x4" }] }] },
        fragment: {
          module,
          entryPoint: "fs",
          targets: [{
            format,
            blend: {
              color: { srcFactor: "one", dstFactor: "one-minus-src-alpha" },
              alpha: { srcFactor: "one", dstFactor: "one-minus-src-alpha" },
            },
          }],
        },
        primitive: { topology: "line-list" },
      });
      const bind = device.createBindGroup({ layout: pipeline.getBindGroupLayout(0), entries: [{ binding: 0, resource: { buffer: ubuf } }] });
      const [m0, m1, m2] = tokenRgb("--color-fg-muted");
      const [b0, b1, b2] = tokenRgb("--color-brand");
      const u = new Float32Array([0, 0, 0, 0, m0, m1, m2, 0.38, b0, b1, b2, 0.62]);
      const t0 = performance.now();

      const frame = (now: number) => {
        if (cancelled) return;
        u[0] = 8 + (now - t0) / 1000; // start mid-motion so the first frame already has depth
        device.queue.writeBuffer(ubuf, 0, u);
        const enc = device.createCommandEncoder();
        const pass = enc.beginRenderPass({
          colorAttachments: [{ view: ctx.getCurrentTexture().createView(), clearValue: { r: 0, g: 0, b: 0, a: 0 }, loadOp: "clear", storeOp: "store" }],
        });
        pass.setPipeline(pipeline);
        pass.setBindGroup(0, bind);
        pass.setVertexBuffer(0, vbuf);
        pass.draw(verts.length / 4);
        pass.end();
        device.queue.submit([enc.finish()]);
        if (!still) raf = requestAnimationFrame(frame);
      };
      raf = requestAnimationFrame(frame);
      canvas.dataset.renderer = "webgpu";
    }

    init().catch(() => {
      if (cancelled || !canvas) return;
      drawFallback(canvas, verts);
      canvas.dataset.renderer = "canvas2d";
    });

    return () => {
      cancelled = true;
      cancelAnimationFrame(raf);
      device?.destroy();
    };
  }, []);

  return <canvas ref={ref} className="seal" width={SIZE} height={SIZE} aria-hidden="true" />;
}
