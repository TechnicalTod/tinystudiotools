"""Check: selected meshes have no construction history."""

from __future__ import annotations

from ..runner import CheckContext, CheckResult


def run(ctx: CheckContext) -> CheckResult:
    has_history = ctx.host.selection_has_history()
    return CheckResult(
        check_id=ctx.spec.id,
        message=(
            "No construction history on selection."
            if not has_history
            else "Selection has construction history."
        ),
        severity="pass" if not has_history else ctx.spec.severity,
        passed=not has_history,
    )
