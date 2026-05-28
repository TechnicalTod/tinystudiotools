"""Pre-publish check registry.

To add a check:

1. Drop a module in ``checks/plugins/`` exposing one function
   ``def run(ctx: CheckContext) -> CheckResult``.
2. Register it below in ``DEFAULT_CHECKS`` (one line).
3. Reference its id under the matching publish type in
   ``configs/asset_publish_schema.json``.

To remove a check, delete its JSON entry. The plugin file can stay; only
schema entries trigger execution.
"""

from __future__ import annotations

from typing import Callable, Dict, Optional

from .plugins import (
    asset_name_pascal_case,
    content_under_env_group,
    materials_m_prefix_pascal,
    nodes_exist,
    no_history_on_selection,
    root_joint_exists,
    root_joint_puppet_attrs,
    selection_not_empty,
)
from .runner import CheckContext, CheckResult


CheckFn = Callable[[CheckContext], CheckResult]


DEFAULT_CHECKS: Dict[str, CheckFn] = {
    "selection_not_empty": selection_not_empty.run,
    "no_history_on_selection": no_history_on_selection.run,
    "nodes_exist": nodes_exist.run,
    "asset_name_pascal_case": asset_name_pascal_case.run,
    "materials_m_prefix_pascal": materials_m_prefix_pascal.run,
    "root_joint_exists": root_joint_exists.run,
    "root_joint_puppet_attrs": root_joint_puppet_attrs.run,
    "content_under_env_group": content_under_env_group.run,
}


def get_check(check_id: str) -> Optional[CheckFn]:
    return DEFAULT_CHECKS.get(check_id)
