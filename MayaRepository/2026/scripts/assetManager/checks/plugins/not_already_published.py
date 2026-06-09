"""Check: selected mesh is not already published."""

from __future__ import annotations

from ..runner import CheckContext, CheckResult


def run(ctx: CheckContext) -> CheckResult:
    published = ctx.host.selection_has_published_mesh()
    ok = not published
    return CheckResult(
        check_id=ctx.spec.id,
        message=(
            "Selection is not already published."
            if ok
            else "Unpublish or select a different mesh — published objects cannot be republished."
        ),
        severity="pass" if ok else ctx.spec.severity,
        passed=ok,
    )
