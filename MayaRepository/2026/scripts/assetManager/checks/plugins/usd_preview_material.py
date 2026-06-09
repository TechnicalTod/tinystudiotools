"""Check: selected mesh uses legacy ``usdPreviewSurface`` material."""

from __future__ import annotations

from ..runner import CheckContext, CheckResult


def run(ctx: CheckContext) -> CheckResult:
    ok = ctx.host.selection_has_usd_preview_material()
    return CheckResult(
        check_id=ctx.spec.id,
        message=(
            "Selection uses USD Preview (usdPreviewSurface) material."
            if ok
            else "Assign a legacy usdPreviewSurface material before publishing."
        ),
        severity="pass" if ok else ctx.spec.severity,
        passed=ok,
    )
