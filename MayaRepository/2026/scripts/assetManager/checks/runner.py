"""Run pre-publish checks from schema.

The runner is intentionally thin: for every :class:`CheckSpec` in the
publish type's ``checks`` array it builds a :class:`CheckContext` and asks
the registry for a handler. Adding or removing a check is therefore a JSON
edit plus, at most, a one-line registration in
``assetManager.checks.registry``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..core.schema import AssetPublishSchema, CheckSpec
from ..core.target import AssetPublishTarget
from ..host import MayaHost


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    message: str
    severity: str  # "error" | "warning" | "pass"
    passed: bool


@dataclass(frozen=True)
class CheckContext:
    """Everything a check plugin needs to make a decision."""

    host: MayaHost
    spec: CheckSpec
    publish_type: str
    target: Optional[AssetPublishTarget] = None

    @property
    def params(self) -> Dict[str, Any]:
        return self.spec.params


class CheckRunner:
    def __init__(self, schema: AssetPublishSchema, host: MayaHost) -> None:
        self._schema = schema
        self._host = host

    def run(
        self,
        publish_type: str,
        target: Optional[AssetPublishTarget] = None,
    ) -> List[CheckResult]:
        spec = self._schema.get_publish_type(publish_type)

        if not spec.checks:
            return [
                CheckResult(
                    check_id="none",
                    message="No pre-publish checks for this type.",
                    severity="pass",
                    passed=True,
                )
            ]

        from .registry import get_check  # lazy to keep import graph simple

        results: List[CheckResult] = []
        for check in spec.checks:
            ctx = CheckContext(
                host=self._host,
                spec=check,
                publish_type=publish_type,
                target=target,
            )
            fn = get_check(check.id)
            if fn is None:
                results.append(
                    CheckResult(
                        check_id=check.id,
                        message=(
                            f"Unknown check {check.id!r} — register it in "
                            "checks/registry.py."
                        ),
                        severity="warning",
                        passed=True,
                    )
                )
                continue
            try:
                result = fn(ctx)
            except Exception as exc:  # noqa: BLE001 - surface as advisory only
                results.append(
                    CheckResult(
                        check_id=check.id,
                        message=f"{check.id} errored: {exc}",
                        severity=check.severity,
                        passed=False,
                    )
                )
                continue
            results.append(self._normalize(result, check))
        return results

    def has_blocking_errors(self, results: List[CheckResult]) -> bool:
        """Whether any error-severity check failed.

        Retained for the optional strict-pipeline follow-up. The advisory UI
        does **not** use this to gate Publish.
        """
        return any(not r.passed and r.severity == "error" for r in results)

    @staticmethod
    def _normalize(result: CheckResult, spec: CheckSpec) -> CheckResult:
        """Force severity to come from the JSON spec when the check fails.

        Plugins return ``severity="pass"`` for success; the spec's configured
        severity (``error`` / ``warning``) drives styling on failure.
        """
        if result.passed:
            return result
        if result.severity == spec.severity:
            return result
        return CheckResult(
            check_id=result.check_id,
            message=result.message,
            severity=spec.severity,
            passed=False,
        )
