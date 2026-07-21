"""
Agent Config Store
Reads/writes configs/agent_configs.json so agent behavior (model, system
prompt, temperature, ...) can be customized from the web UI without a
process restart.
"""

import json
import os
import threading
from pathlib import Path
from typing import Dict, List, Optional

CONFIG_DIR = Path(__file__).resolve().parent.parent / "configs"
CONFIG_PATH = CONFIG_DIR / "agent_configs.json"
MODEL_MAP_PATH = CONFIG_DIR / "model_map.json"

_lock = threading.Lock()

VALID_ROLES = {"thinker", "validator", "executor"}
VALID_TARGETS = {"gpu_master", "gpu_worker", "cpu_cluster"}

EDITABLE_FIELDS = {
    "display_name", "role", "target", "model",
    "temperature", "max_tokens", "enabled", "system_prompt",
}


class AgentConfigError(ValueError):
    pass


def _read_raw() -> Dict:
    if not CONFIG_PATH.exists():
        return {"agents": []}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_raw(data: Dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = CONFIG_PATH.with_suffix(".json.tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, CONFIG_PATH)


def list_agents() -> List[Dict]:
    with _lock:
        return _read_raw().get("agents", [])


def get_agent(key: str) -> Optional[Dict]:
    for agent in list_agents():
        if agent.get("key") == key:
            return agent
    return None


def get_agent_or_default(key: str, default: Dict) -> Dict:
    """Used by orchestrator code so a deleted/missing entry still works."""
    agent = get_agent(key)
    if agent and agent.get("enabled", True):
        return agent
    return default


def _validate_fields(fields: Dict, partial: bool) -> None:
    unknown = set(fields) - EDITABLE_FIELDS
    if unknown:
        raise AgentConfigError(f"Unknown field(s): {', '.join(sorted(unknown))}")

    if "role" in fields and fields["role"] not in VALID_ROLES:
        raise AgentConfigError(f"role must be one of {sorted(VALID_ROLES)}")

    if "target" in fields and fields["target"] not in VALID_TARGETS:
        raise AgentConfigError(f"target must be one of {sorted(VALID_TARGETS)}")

    if "temperature" in fields:
        temp = fields["temperature"]
        if not isinstance(temp, (int, float)) or not (0 <= temp <= 2):
            raise AgentConfigError("temperature must be a number between 0 and 2")

    if "max_tokens" in fields:
        tokens = fields["max_tokens"]
        if not isinstance(tokens, int) or not (1 <= tokens <= 32768):
            raise AgentConfigError("max_tokens must be an integer between 1 and 32768")

    if not partial:
        required = {"role", "target", "model", "system_prompt"}
        missing = required - set(fields)
        if missing:
            raise AgentConfigError(f"Missing required field(s): {', '.join(sorted(missing))}")


def create_agent(key: str, fields: Dict) -> Dict:
    if not key or not key.replace("_", "").isalnum():
        raise AgentConfigError("key must be alphanumeric/underscore only")

    _validate_fields(fields, partial=False)

    with _lock:
        data = _read_raw()
        agents = data.setdefault("agents", [])

        if any(a.get("key") == key for a in agents):
            raise AgentConfigError(f"Agent '{key}' already exists")

        record = {
            "key": key,
            "display_name": fields.get("display_name", key),
            "role": fields["role"],
            "target": fields["target"],
            "model": fields["model"],
            "temperature": fields.get("temperature", 0.7),
            "max_tokens": fields.get("max_tokens", 2048),
            "enabled": fields.get("enabled", True),
            "system_prompt": fields["system_prompt"],
        }
        agents.append(record)
        _write_raw(data)
        return record


def update_agent(key: str, fields: Dict) -> Dict:
    _validate_fields(fields, partial=True)

    with _lock:
        data = _read_raw()
        agents = data.setdefault("agents", [])

        for agent in agents:
            if agent.get("key") == key:
                agent.update(fields)
                _write_raw(data)
                return agent

        raise AgentConfigError(f"Agent '{key}' not found")


def delete_agent(key: str) -> None:
    with _lock:
        data = _read_raw()
        agents = data.get("agents", [])
        remaining = [a for a in agents if a.get("key") != key]

        if len(remaining) == len(agents):
            raise AgentConfigError(f"Agent '{key}' not found")

        data["agents"] = remaining
        _write_raw(data)


def list_available_models() -> List[Dict]:
    if not MODEL_MAP_PATH.exists():
        return []
    with open(MODEL_MAP_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("model_map", [])
