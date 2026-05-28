"""Check: every published mesh lives under a single top-level ``ENV`` group.

Edge cases:

* Empty scene — passes (nothing to validate).
* ``ENV`` exists but contains no meshes — passes (warned via the empty scene
  branch); the export step is responsible for raising during publish.
* ``ENV`` missing — fails and lists the meshes that would have been published.

Cameras / lights are intentionally **not** checked here in v1; only mesh
shapes are required to live under ``ENV``.

Params:
    group_name (str, default ``"ENV"``):
        Required parent group name (case-sensitive — ``Env`` is rejected).
"""

from __future__ import annotations

from ..runner import CheckContext, CheckResult


def run(ctx: CheckContext) -> CheckResult:
    group_name = str(ctx.params.get("group_name", "ENV"))

    if not ctx.host.node_exists(group_name):
        outside = ctx.host.meshes_outside_group(group_name)
        if not outside:
            return CheckResult(
                check_id=ctx.spec.id,
                message=(
                    f"Group {group_name!r} not found and the scene is empty — "
                    "nothing to publish."
                ),
                severity="pass",
                passed=True,
            )
        return CheckResult(
            check_id=ctx.spec.id,
            message=(
                f"Group {group_name!r} is missing — wrap layout content under it. "
                f"{len(outside)} mesh(es) outside."
            ),
            severity=ctx.spec.severity,
            passed=False,
        )

    outside = ctx.host.meshes_outside_group(group_name)
    if not outside:
        return CheckResult(
            check_id=ctx.spec.id,
            message=f"All layout meshes live under {group_name!r}.",
            severity="pass",
            passed=True,
        )

    preview = ", ".join(outside[:3])
    if len(outside) > 3:
        preview += f", … (+{len(outside) - 3} more)"
    return CheckResult(
        check_id=ctx.spec.id,
        message=(
            f"{len(outside)} mesh(es) outside {group_name!r}: {preview}."
        ),
        severity=ctx.spec.severity,
        passed=False,
    )
