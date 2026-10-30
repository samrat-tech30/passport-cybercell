/** Line-art scenes for empty and idle states. Black ink, one yellow highlighter accent, decorative only. */

type Scene = "passport" | "unplugged" | "ledger";

export function Illustration({ scene, className = "" }: { scene: Scene; className?: string }) {
  return (
    <svg className={`ill ill--${scene} ${className}`} viewBox="0 0 240 180" aria-hidden="true" focusable="false">
      {scene === "passport" && <Passport />}
      {scene === "unplugged" && <Unplugged />}
      {scene === "ledger" && <Ledger />}
    </svg>
  );
}

/** An open passport; a rubber stamp hovers over the right page, about to land. */
function Passport() {
  return (
    <>
      <path className="ill__paper" d="M28 78 Q74 68 120 78 Q166 68 212 78 V156 Q166 146 120 156 Q74 146 28 156 Z" />
      <path d="M120 78 V156" />
      {/* left page: photo and details */}
      <rect x="42" y="90" width="26" height="32" rx="3" />
      <circle cx="55" cy="102" r="5" />
      <path d="M46 120 Q55 110 64 120" />
      <path d="M78 94 H106 M78 103 H100 M78 112 H104" />
      <rect className="ill__marker" x="40" y="130" width="40" height="8" rx="2" />
      <path d="M42 134 H78 M88 134 H106" />
      {/* right page: a faint earlier stamp and the landing zone */}
      <circle cx="148" cy="116" r="16" strokeDasharray="2 4" />
      <path d="M176 96 H198 M176 104 H192" />
      {/* the stamp */}
      <g className="ill__float">
        <circle cx="168" cy="22" r="7" />
        <path d="M165 29 V40 M171 29 V40" />
        <rect className="ill__paper" x="152" y="40" width="32" height="11" rx="3" />
        <path d="M156 51 V55 H180 V51" />
      </g>
      <path className="ill__hint" d="M160 66 V70 M168 64 V70 M176 66 V70" />
    </>
  );
}

/** A plug pulled out of its socket. */
function Unplugged() {
  return (
    <>
      <rect className="ill__paper" x="30" y="62" width="56" height="64" rx="10" />
      <rect x="44" y="80" width="6" height="14" rx="2" />
      <rect x="66" y="80" width="6" height="14" rx="2" />
      <circle cx="58" cy="108" r="3" />
      <rect className="ill__marker" x="96" y="88" width="22" height="14" rx="3" />
      <path d="M98 84 L104 90 M108 82 V90 M118 84 L112 90" />
      <path d="M124 84 H134 M124 104 H134" />
      <rect className="ill__paper" x="134" y="74" width="34" height="40" rx="8" />
      <path d="M168 94 C196 94 196 140 214 140 H226" />
    </>
  );
}

/** An open ledger with empty ruled lines and a pen resting on it. */
function Ledger() {
  return (
    <>
      <path className="ill__paper" d="M28 52 Q74 42 120 52 Q166 42 212 52 V150 Q166 140 120 150 Q74 140 28 150 Z" />
      <path d="M120 52 V150" />
      <rect className="ill__marker" x="40" y="68" width="44" height="8" rx="2" />
      <path d="M42 72 H104 M42 88 H104 M42 104 H104 M42 120 H104" />
      <path d="M136 72 H198 M136 88 H198 M136 104 H198 M136 120 H198" />
      <g className="ill__float ill__float--slow">
        <path className="ill__paper" d="M150 140 L196 94 L204 102 L158 148 Z" />
        <path d="M150 140 L146 152 L158 148" />
        <path d="M190 100 L198 108" />
      </g>
    </>
  );
}
