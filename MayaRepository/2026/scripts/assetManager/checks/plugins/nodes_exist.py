"""Check: a configured list of nodes all exist in the scene."""

from __future__ import annotations

from ..runner import CheckContext, CheckResult


def run(ctx: CheckContext) -> CheckResult:
    names = ctx.spec.nodes  # legacy convenience accessor on CheckSpec
    if not names:
        return CheckResult(
            check_id=ctx.spec.id,
            message="No nodes configured for this check.",
            severity="warning",
            passed=True,
        )
    missing = ctx.host.nodes_exist(list(names))
    ok = not missing
    return CheckResult(
        check_id=ctx.spec.id,
        message=(
            "Required nodes present."
            if ok
            else f"Missing nodes: {', '.join(missing)}"
        ),
        severity="pass" if ok else ctx.spec.severity,
        passed=ok,
    )
