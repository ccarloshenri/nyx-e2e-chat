from __future__ import annotations

import json
import statistics
from dataclasses import asdict, dataclass, field
from pathlib import Path


HISTOGRAM_BUCKETS_MS: tuple[float, ...] = (5, 10, 25, 50, 100, 250, 500, 1_000, 2_000)


@dataclass(slots=True)
class FailureRecord:
    request_id: int
    status_code: int | None
    latency_ms: float
    error: str
    context: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class PhaseMetrics:
    phase_name: str
    total_requests: int = 0
    successes: int = 0
    failures: int = 0
    response_times_ms: list[float] = field(default_factory=list)
    failure_records: list[FailureRecord] = field(default_factory=list)
    started_at: float = 0.0
    finished_at: float = 0.0

    def record_success(self, latency_ms: float) -> None:
        self.total_requests += 1
        self.successes += 1
        self.response_times_ms.append(latency_ms)

    def record_failure(
        self,
        *,
        request_id: int,
        latency_ms: float,
        error: str,
        status_code: int | None = None,
        context: dict[str, str] | None = None,
    ) -> None:
        self.total_requests += 1
        self.failures += 1
        self.response_times_ms.append(latency_ms)
        self.failure_records.append(
            FailureRecord(
                request_id=request_id,
                status_code=status_code,
                latency_ms=latency_ms,
                error=error,
                context=context or {},
            )
        )

    @property
    def duration_seconds(self) -> float:
        return max(self.finished_at - self.started_at, 0.0)

    @property
    def error_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.failures / self.total_requests) * 100.0

    @property
    def throughput(self) -> float:
        if self.duration_seconds <= 0:
            return 0.0
        return self.total_requests / self.duration_seconds

    @property
    def avg_response_time_ms(self) -> float:
        return statistics.fmean(self.response_times_ms) if self.response_times_ms else 0.0

    @property
    def median_response_time_ms(self) -> float:
        return statistics.median(self.response_times_ms) if self.response_times_ms else 0.0

    @property
    def min_response_time_ms(self) -> float:
        return min(self.response_times_ms) if self.response_times_ms else 0.0

    @property
    def max_response_time_ms(self) -> float:
        return max(self.response_times_ms) if self.response_times_ms else 0.0

    def histogram(self, width: int = 24) -> list[str]:
        if not self.response_times_ms:
            return ["No response times recorded."]

        counts = [0 for _ in range(len(HISTOGRAM_BUCKETS_MS) + 1)]
        for latency_ms in self.response_times_ms:
            placed = False
            for index, upper_bound in enumerate(HISTOGRAM_BUCKETS_MS):
                if latency_ms <= upper_bound:
                    counts[index] += 1
                    placed = True
                    break
            if not placed:
                counts[-1] += 1

        max_count = max(counts) or 1
        rows: list[str] = []
        lower_bound = 0.0
        for index, count in enumerate(counts):
            if index < len(HISTOGRAM_BUCKETS_MS):
                upper_bound = HISTOGRAM_BUCKETS_MS[index]
                label = f"{lower_bound:>6.0f}-{upper_bound:<6.0f} ms"
                lower_bound = upper_bound
            else:
                label = f"{HISTOGRAM_BUCKETS_MS[-1]:>6.0f}+       ms"
            bar_length = int(round((count / max_count) * width))
            rows.append(f"{label} | {'#' * bar_length} ({count})")
        return rows

    def to_dict(self) -> dict:
        return {
            "phase_name": self.phase_name,
            "total_requests": self.total_requests,
            "successes": self.successes,
            "failures": self.failures,
            "error_rate": self.error_rate,
            "duration_seconds": self.duration_seconds,
            "throughput": self.throughput,
            "avg_response_time_ms": self.avg_response_time_ms,
            "median_response_time_ms": self.median_response_time_ms,
            "min_response_time_ms": self.min_response_time_ms,
            "max_response_time_ms": self.max_response_time_ms,
            "histogram": self.histogram(),
            "failure_records": [asdict(record) for record in self.failure_records],
        }


def render_report(metrics: PhaseMetrics) -> str:
    return "\n".join(
        [
            "Load Test Report",
            "",
            f"Phase: {metrics.phase_name}",
            "",
            f"Total Requests: {metrics.total_requests}",
            f"Success: {metrics.successes}",
            f"Failures: {metrics.failures}",
            f"Error Rate: {metrics.error_rate:.2f}%",
            "",
            "Performance:",
            f"Avg Response Time: {metrics.avg_response_time_ms:.2f} ms",
            f"Median Response Time: {metrics.median_response_time_ms:.2f} ms",
            f"Min Response Time: {metrics.min_response_time_ms:.2f} ms",
            f"Max Response Time: {metrics.max_response_time_ms:.2f} ms",
            f"Throughput: {metrics.throughput:.2f} req/s",
            "",
            "Response Time Histogram:",
            *metrics.histogram(),
        ]
    )


def export_json_report(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def export_failure_log(path: Path, failures: list[FailureRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(asdict(record)) for record in failures),
        encoding="utf-8",
    )
