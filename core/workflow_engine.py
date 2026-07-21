"""
Generic execution engine for visually-designed agent workflows
(configs/workflow_configs/*.json).

Nodes are wired together implicitly: a node runs once every variable name
listed in its "inputs" has been produced by some earlier node's "outputs"
(the same convention already used by configs/workflow_configs/debate_workflow.json).
"""

import json
import os
from typing import Dict, List, Optional

from services.ollama_client import OllamaClient
from services import agent_config_store
from utils.logger import setup_logger

logger = setup_logger(__name__)

RUNNABLE_TYPES = {"THINKER_AGENT", "VALIDATOR_AGENT", "EXECUTOR_AGENT"}


class WorkflowExecutionError(Exception):
    pass


def _client_for_target(target: str) -> OllamaClient:
    url = os.getenv("OLLAMA_WORKER_URL") if target == "gpu_worker" else os.getenv("OLLAMA_MASTER_URL")
    if not url:
        raise WorkflowExecutionError(f"No Ollama endpoint configured for target '{target}'")
    return OllamaClient(url)


def _node_settings(node: Dict) -> Dict:
    """Resolve model/target/temperature/system_prompt for a node, optionally
    inheriting from a saved agent config via node['agentKey']."""

    settings = {
        "target": "gpu_master",
        "model": os.getenv("MODEL_GPT_THINKER", "qwen2.5:32b"),
        "temperature": 0.7,
        "max_tokens": 2048,
        "system_prompt": "",
    }

    agent_key = node.get("agentKey")
    if agent_key:
        stored = agent_config_store.get_agent(agent_key)
        if stored:
            for field in ("target", "model", "temperature", "max_tokens", "system_prompt"):
                if stored.get(field) is not None:
                    settings[field] = stored[field]

    # Per-node overrides win over the referenced agent config
    for field in ("model", "target", "temperature", "max_tokens"):
        if node.get(field) is not None:
            settings[field] = node[field]
    if node.get("systemPrompt"):
        settings["system_prompt"] = node["systemPrompt"]

    return settings


async def run_workflow(workflow: Dict, query: str) -> Dict:
    """Execute a workflow graph against a single user query, returning the
    final answer plus a per-node trace useful for debugging in the builder UI."""

    nodes = {n["id"]: n for n in workflow.get("nodes", [])}
    if not nodes:
        raise WorkflowExecutionError("Workflow has no nodes")

    start_nodes = [n for n in nodes.values() if n["type"] == "START_NODE"]
    end_nodes = [n for n in nodes.values() if n["type"] == "END_NODE"]
    if len(start_nodes) != 1 or len(end_nodes) != 1:
        raise WorkflowExecutionError("Workflow must have exactly one START_NODE and one END_NODE")

    variables: Dict[str, str] = {}
    for out in start_nodes[0].get("outputs", []):
        variables[out["output"]] = query

    pending = {nid: n for nid, n in nodes.items() if n["type"] != "START_NODE"}
    trace: List[Dict] = [{
        "node_id": start_nodes[0]["id"], "type": "START_NODE", "output_preview": query[:200]
    }]
    validation_result: Optional[Dict] = None

    progressed = True
    while pending and progressed:
        progressed = False

        for node_id in list(pending.keys()):
            node = pending[node_id]
            required_inputs = [i["input"] for i in node.get("inputs", [])]

            if not all(name in variables for name in required_inputs):
                continue  # dependencies not ready yet

            if node["type"] == "END_NODE":
                final_var = required_inputs[0] if required_inputs else None
                trace.append({
                    "node_id": node_id, "type": "END_NODE",
                    "output_preview": variables.get(final_var, "")[:200]
                })
                del pending[node_id]
                progressed = True
                continue

            if node["type"] not in RUNNABLE_TYPES:
                raise WorkflowExecutionError(f"Unsupported node type '{node['type']}' for node '{node_id}'")

            settings = _node_settings(node)
            input_text = "\n".join(f"[{name}]\n{variables[name]}" for name in required_inputs)
            prompt = f"{settings['system_prompt']}\n\n{input_text}" if settings["system_prompt"] else input_text

            client = _client_for_target(settings["target"])
            try:
                raw_output = await client.generate(
                    model=settings["model"],
                    prompt=prompt,
                    max_tokens=settings["max_tokens"],
                    temperature=settings["temperature"]
                )
            except Exception as e:
                raise WorkflowExecutionError(f"Node '{node_id}' failed: {e}")

            if isinstance(raw_output, dict):
                raw_output = raw_output.get("response", "") or str(raw_output)

            if node["type"] == "VALIDATOR_AGENT":
                try:
                    validation_result = json.loads(raw_output)
                except Exception:
                    validation_result = {"score": None, "reason": "Parse error", "raw": raw_output[:500]}
                # Pass through the answer being validated rather than the score blob itself
                output_text = variables[required_inputs[-1]] if required_inputs else raw_output
            else:
                output_text = raw_output

            outputs = node.get("outputs", [])
            if outputs:
                variables[outputs[0]["output"]] = output_text

            trace.append({
                "node_id": node_id,
                "type": node["type"],
                "model": settings["model"],
                "output_preview": output_text[:200]
            })

            del pending[node_id]
            progressed = True

    if pending:
        stuck = ", ".join(pending.keys())
        raise WorkflowExecutionError(f"Workflow stalled - unresolved dependencies for node(s): {stuck}")

    final_var = end_nodes[0]["inputs"][0]["input"] if end_nodes[0].get("inputs") else None

    return {
        "answer": variables.get(final_var, ""),
        "validation": validation_result,
        "trace": trace,
    }
