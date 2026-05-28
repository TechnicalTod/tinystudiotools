"""Check: every assigned material is named ``M_<PascalCase>``.

Default Maya materials (``lambert1`` etc.) are excluded by the host so
that only artist-authored shaders are validated.

Params:
    prefix (str, default ``"M_"``):
        Required prefix on the material name.
"""

from __future__ import annotations

import re

from ..runner import CheckContext, CheckResult


_PASCAL = re.compile(r"^[A-Z][A-Za-z0-9]*$")


def run(ctx: CheckContext) -> CheckResult:
    prefix = str(ctx.params.get("prefix", "M_"))
    materials = ctx.host.list_assignable_materials()
    if not materials:
        return CheckResult(
            check_id=ctx.spec.id,
            message="No assigned materials found.",
            severity="pass",
            passed=True,
        )

    bad: list[str] = []
    for name in materials:
        if not name.startswith(prefix):
            bad.append(name)
            continue
        remainder = name[len(prefix):]
        if not _PASCAL.match(remainder):
            bad.append(name)

    ok = not bad
    return CheckResult(
        check_id=ctx.spec.id,
        message=(
            f"All materials use {prefix}<PascalCase> naming."
            if ok
            else f"Materials not matching {prefix}<PascalCase>: {', '.join(bad)}."
        ),
        severity="pass" if ok else ctx.spec.severity,
        passed=ok,
    )
