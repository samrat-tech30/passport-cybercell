from __future__ import annotations

from app.contracts import Trust
from app.gate.capsule import build_capsule
from app.gate.decide import GateContext
from app.gate.policy import load_policy
from app.gate.segments import new_store
from app.tools.world import World


def make_ctx(
    user_request: str, inbox: str = "base", emails_read: bool = False, fault: str | None = None
) -> GateContext:
    world = World(inbox=inbox)
    store = new_store(user_request, world)
    if emails_read:
        store.ingest("list_unread_emails", {}, world.list_unread_emails())
    policy = load_policy()
    return GateContext(
        session_id="ses_test",
        policy=policy,
        store=store,
        capsule=build_capsule(user_request),
        world=world,
        profile=policy.default_profile,
        fault=fault,
    )


def add_untrusted(ctx: GateContext, seg_id: str, text: str) -> None:
    ctx.store.add(seg_id, f"Test source {seg_id}", Trust.UNTRUSTED, text)
