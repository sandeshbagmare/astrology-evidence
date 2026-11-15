from typing import Any, Literal
Truth = Literal['true', 'false', 'unknown']
def applicability(rule: dict[str, Any], facts: list[dict[str, Any]]) -> Truth:
    required = rule.get('required_fact_kinds', [])
    if not isinstance(required, list): return 'unknown'
    kinds = {f.get('kind') for f in facts if isinstance(f, dict)}
    if any(kind not in kinds for kind in required): return 'unknown'
    if rule.get('predicate') == 'always': return 'true'
    if rule.get('predicate') == 'fact_equals':
        for fact in facts:
            if fact.get('kind') == rule.get('kind'): return 'true' if fact.get('value') == rule.get('value') else 'false'
    return 'unknown'
def reviewed_rules(rules: list[dict[str, Any]], facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in rules if r.get('reviewed') is True and applicability(r, facts) == 'true']
