from abc import ABC, abstractmethod
from typing import List, Tuple, Dict


class ValidationRule(ABC):
    """Base class for validation rules"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.enabled = True

    @abstractmethod
    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """Run validation and return (passed, errors, warnings)"""
        pass


class ValidationManager:
    """Manages validation rules and execution"""

    def __init__(self):
        self.rules: List[ValidationRule] = []
        self.setup_default_rules()

    def setup_default_rules(self):
        """Setup default validation rules"""
        try:
            from .rules import NamingConventionRule, SceneCleanupRule

            self.rules = [NamingConventionRule(), SceneCleanupRule()]
        except ImportError:
            # Fallback if rules module is not available
            pass

    def add_rule(self, rule: ValidationRule):
        """Add a custom validation rule"""
        self.rules.append(rule)

    def remove_rule(self, rule_name: str):
        """Remove a validation rule by name"""
        self.rules = [rule for rule in self.rules if rule.name != rule_name]

    def get_rule(self, rule_name: str) -> ValidationRule:
        """Get a validation rule by name"""
        for rule in self.rules:
            if rule.name == rule_name:
                return rule
        return None

    def run_validation(
        self, enabled_rules: List[str] = None
    ) -> Dict[str, Tuple[bool, List[str], List[str]]]:
        """Run validation rules and return results"""
        results = {}

        for rule in self.rules:
            if not rule.enabled:
                continue

            if enabled_rules and rule.name not in enabled_rules:
                continue

            try:
                passed, errors, warnings = rule.validate()
                results[rule.name] = (passed, errors, warnings)
            except Exception as e:
                results[rule.name] = (False, [f"Validation error: {str(e)}"], [])

        return results

    def get_overall_status(
        self, results: Dict[str, Tuple[bool, List[str], List[str]]]
    ) -> Tuple[bool, int, int]:
        """Get overall validation status"""
        total_errors = 0
        total_warnings = 0
        all_passed = True

        for passed, errors, warnings in results.values():
            if not passed:
                all_passed = False
            total_errors += len(errors)
            total_warnings += len(warnings)

        return all_passed, total_errors, total_warnings

    def enable_rule(self, rule_name: str):
        """Enable a specific validation rule"""
        rule = self.get_rule(rule_name)
        if rule:
            rule.enabled = True

    def disable_rule(self, rule_name: str):
        """Disable a specific validation rule"""
        rule = self.get_rule(rule_name)
        if rule:
            rule.enabled = False

    def list_rules(self) -> List[Dict[str, any]]:
        """List all validation rules with their status"""
        return [
            {"name": rule.name, "description": rule.description, "enabled": rule.enabled}
            for rule in self.rules
        ]
