"""Check: at least one node is selected."""

from __future__ import annotations

from ..runner import CheckContext, CheckResult


def run(ctx: CheckContext) -> CheckResult:
    ok = ctx.host.selection_not_empty()
    return CheckResult(
        check_id=ctx.spec.id,
        message=(
            "Selection is not empty."
            if ok
            else "Select at least one object to publish."
        ),
        severity="pass" if ok else ctx.spec.severity,
        passed=ok,
    )
