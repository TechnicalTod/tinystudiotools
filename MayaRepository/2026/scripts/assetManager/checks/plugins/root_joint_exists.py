"""Check: the rig root joint exists in the scene.

Params:
    root_joint_name (str, default ``"root_joint"``):
        Name of the root joint to look up.
"""

from __future__ import annotations

from ..runner import CheckContext, CheckResult


def run(ctx: CheckContext) -> CheckResult:
    name = str(ctx.params.get("root_joint_name", "root_joint"))
    ok = ctx.host.node_exists(name)
    return CheckResult(
        check_id=ctx.spec.id,
        message=(
            f"Root joint {name!r} present."
            if ok
            else f"Root joint {name!r} not found."
        ),
        severity="pass" if ok else ctx.spec.severity,
        passed=ok,
    )
