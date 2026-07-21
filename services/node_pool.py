"""
CPU Cluster Node Pool
Round-robin selection across OLLAMA_CPU_NODES so agents/workflow nodes
targeting "cpu_cluster" spread load across all configured CPU Ollama servers.
"""

import itertools
import os
import threading
from typing import List, Optional

_lock = threading.Lock()
_cycle = None
_cached_nodes: Optional[List[str]] = None


def get_cpu_nodes() -> List[str]:
    raw = os.getenv("OLLAMA_CPU_NODES", "")
    return [n.strip() for n in raw.split(",") if n.strip()]


def next_cpu_node() -> Optional[str]:
    """Return the next CPU node URL in round-robin order, or None if none are configured."""

    global _cycle, _cached_nodes

    nodes = get_cpu_nodes()
    if not nodes:
        return None

    with _lock:
        if nodes != _cached_nodes:
            _cached_nodes = nodes
            _cycle = itertools.cycle(nodes)
        return next(_cycle)
