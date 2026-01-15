from typing import Dict, Any
from .agents.relations import RelationsAgent
from .core.coordinator import Coordinator


def execute_find_paths(coordinator: Coordinator, params: Dict[str, Any]) -> Dict[str, Any]:
    # bornes du plan
    depth = params.get("depth", 4)
    depth = min(max(int(depth), 1), 4)
    max_paths = params.get("max_paths", 10)
    max_paths = min(max(int(max_paths), 1), 50)
    args = {
        "entity_a": params.get("source_entity") or params.get("entity_a"),
        "type_a": params.get("type_a") or "company",
        "entity_b": params.get("target_entity") or params.get("entity_b"),
        "type_b": params.get("type_b") or "company",
        "year_min": params.get("year_from") or params.get("year_min"),
        "year_max": params.get("year_to") or params.get("year_max"),
        "currency_code": params.get("currency") or params.get("currency_code"),
        "max_paths": max_paths,
    }
    # On délègue au coordinator (RelationsAgent est déjà enregistré)
    result = coordinator.run("find_paths_between_entities", args)
    return {
        "depth_used": depth,
        "max_paths_used": max_paths,
        "result": result,
    }
