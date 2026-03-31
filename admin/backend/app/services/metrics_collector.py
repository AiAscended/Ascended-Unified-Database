import asyncio
import time
from datetime import datetime, timezone

from app.models.schemas import MetricSnapshot


def _read_proc_stat() -> dict[str, float]:
    stats: dict[str, float] = {}
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                parts = line.split()
                if parts[0] in ("MemTotal:", "MemAvailable:"):
                    stats[parts[0].rstrip(":")] = int(parts[1]) * 1024
    except OSError:
        pass
    try:
        with open("/proc/loadavg") as f:
            load = f.read().split()
            stats["load_1m"] = float(load[0])
            stats["load_5m"] = float(load[1])
            stats["load_15m"] = float(load[2])
    except OSError:
        pass
    return stats


def _prometheus_metrics() -> list[MetricSnapshot]:
    snapshots: list[MetricSnapshot] = []
    try:
        from prometheus_client import REGISTRY
        now = datetime.now(timezone.utc)
        for metric in REGISTRY.collect():
            for sample in metric.samples:
                snapshots.append(
                    MetricSnapshot(
                        timestamp=now,
                        name=sample.name,
                        value=sample.value,
                        labels={k: str(v) for k, v in sample.labels.items()},
                    )
                )
    except Exception:
        pass
    return snapshots


async def collect_metrics() -> list[MetricSnapshot]:
    now = datetime.now(timezone.utc)
    snapshots: list[MetricSnapshot] = []

    proc_stats = await asyncio.get_event_loop().run_in_executor(None, _read_proc_stat)
    for name, value in proc_stats.items():
        snapshots.append(MetricSnapshot(timestamp=now, name=f"system_{name.lower()}", value=value))

    prom_snapshots = await asyncio.get_event_loop().run_in_executor(None, _prometheus_metrics)
    snapshots.extend(prom_snapshots)

    return snapshots


async def collect_metrics_dict() -> dict:
    metrics = await collect_metrics()
    proc_stats = await asyncio.get_event_loop().run_in_executor(None, _read_proc_stat)
    mem_total = proc_stats.get("MemTotal", 0)
    mem_available = proc_stats.get("MemAvailable", 0)
    mem_used = mem_total - mem_available if mem_total else 0

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "memory": {
            "total_bytes": mem_total,
            "used_bytes": mem_used,
            "available_bytes": mem_available,
            "used_pct": round(mem_used / mem_total * 100, 2) if mem_total else 0,
        },
        "load": {
            "load_1m": proc_stats.get("load_1m", 0),
            "load_5m": proc_stats.get("load_5m", 0),
            "load_15m": proc_stats.get("load_15m", 0),
        },
        "snapshots": [s.model_dump(mode="json") for s in metrics[:50]],
    }
