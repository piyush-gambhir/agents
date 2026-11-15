import os

import prometheus_client
import psutil

from .. import utils

PROC_INITIALIZE_TIME = prometheus_client.Histogram(
    "lk_agents_proc_initialize_duration_seconds",
    "Time taken to initialize a process",
    ["nodename"],
    buckets=[0.1, 0.5, 1, 2, 5, 10],
)


RUNNING_JOB_GAUGE = prometheus_client.Gauge(
    "lk_agents_active_job_count",
    "Active jobs",
    ["nodename"],
    multiprocess_mode="livesum",
)


CHILD_PROC_GAUGE = prometheus_client.Gauge(
    "lk_agents_child_process_count",
    "Total number of child processes",
    ["nodename"],
    multiprocess_mode="max",
)

CPU_LOAD_GAUGE = prometheus_client.Gauge(
    "lk_agents_worker_load",
    "Worker load percentage",
    ["nodename"],
)


def _update_child_proc_count() -> None:
    """Update child process count metric. Must be called periodically in the main process."""
    try:
        count = len(psutil.Process(os.getpid()).children(recursive=True))
        CHILD_PROC_GAUGE.labels(nodename=utils.nodename()).set(count)
    except Exception:
        pass


def _update_worker_load(worker_load: float) -> None:
    CPU_LOAD_GAUGE.labels(nodename=utils.nodename()).set(worker_load)


def job_started() -> None:
    RUNNING_JOB_GAUGE.labels(nodename=utils.nodename()).inc()


def job_ended() -> None:
    RUNNING_JOB_GAUGE.labels(nodename=utils.nodename()).dec()


def proc_initialized(*, time_elapsed: float) -> None:
    PROC_INITIALIZE_TIME.labels(nodename=utils.nodename()).observe(time_elapsed)
