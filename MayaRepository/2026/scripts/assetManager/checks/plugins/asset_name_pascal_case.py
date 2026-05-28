"""Check: the publish asset name follows PascalCase.

PascalCase here is interpreted loosely: each underscore-separated segment
must start with an uppercase letter, the segment must be alphanumeric, and
the overall name must contain only letters, digits and underscores. The
common ``prop02`` lower-case folder style is therefore *flagged* so the
team converges on ``Prop02`` over time.

Params:
    allow_digits_suffix (bool, default True):
        When True, the trailing digits in a segment (``Prop02``) are
        accepted. When False, only ``Prop`` style is accepted.
"""

from __future__ import annotations

import re

from ..runner import CheckContext, CheckResult


_SEGMENT = re.compile(r"^[A-Z][A-Za-z0-9]*$")
_SEGMENT_LETTERS_ONLY = re.compile(r"^[A-Z][A-Za-z]*$")


def run(ctx: CheckContext) -> CheckResult:
    name = ctx.target.asset if ctx.target else ""
    if not name:
        return CheckResult(
            check_id=ctx.spec.id,
            message="No asset selected; cannot validate name.",
            severity="warning",
            passed=True,
        )

    allow_digits = bool(ctx.params.get("allow_digits_suffix", True))
    pattern = _SEGMENT if allow_digits else _SEGMENT_LETTERS_ONLY

    segments = name.split("_")
    bad = [seg for seg in segments if not pattern.match(seg)]
    ok = not bad
    return CheckResult(
        check_id=ctx.spec.id,
        message=(
            f"Asset name {name!r} is PascalCase."
            if ok
            else f"Asset name {name!r} is not PascalCase. Offending segments: "
            f"{', '.join(bad)}."
        ),
        severity="pass" if ok else ctx.spec.severity,
        passed=ok,
    )
