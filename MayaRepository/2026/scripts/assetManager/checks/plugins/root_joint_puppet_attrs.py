"""Check: the puppet metadata string attributes exist on the rig root joint.

The contract mirrors ``MayaRepository/2026/scripts/riggingTools/addCustomPuppetAttrs.py``
without depending on the script being run as-is.

Params:
    root_joint_name (str, default ``"root_joint"``):
        Node to inspect.
    required_attrs (list[str]):
        Long attribute names that must exist.
    require_non_empty (bool, default ``False``):
        When True, also fail if any required attr is missing or empty.
"""

from __future__ import annotations

from ..runner import CheckContext, CheckResult


_DEFAULT_ATTRS = [
    "assetType",
    "assetName",
    "variant",
    "version",
    "rootJointName",
    "visGeoGroupName",
]


def run(ctx: CheckContext) -> CheckResult:
    root = str(ctx.params.get("root_joint_name", "root_joint"))
    required = list(ctx.params.get("required_attrs") or _DEFAULT_ATTRS)
    require_non_empty = bool(ctx.params.get("require_non_empty", False))

    if not ctx.host.node_exists(root):
        return CheckResult(
            check_id=ctx.spec.id,
            message=f"Root joint {root!r} not found; cannot inspect puppet attrs.",
            severity=ctx.spec.severity,
            passed=False,
        )

    missing: list[str] = []
    empty: list[str] = []
    for attr in required:
        if not ctx.host.attr_exists(root, attr):
            missing.append(attr)
            continue
        if require_non_empty:
            value = ctx.host.attr_string_value(root, attr)
            if not value:
                empty.append(attr)

    if not missing and not empty:
        return CheckResult(
            check_id=ctx.spec.id,
            message=f"All puppet attributes present on {root!r}.",
            severity="pass",
            passed=True,
        )

    parts: list[str] = []
    if missing:
        parts.append(f"missing: {', '.join(missing)}")
    if empty:
        parts.append(f"empty: {', '.join(empty)}")
    return CheckResult(
        check_id=ctx.spec.id,
        message=f"Puppet attribute issues on {root!r} — {'; '.join(parts)}.",
        severity=ctx.spec.severity,
        passed=False,
    )
