from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass
from itertools import count
from time import perf_counter
from typing import Any

from .api import ApiError, NyxApiClient
from .config import BomberConfig, dump_config
from .crypto_sim import build_message_payload
from .metrics import PhaseMetrics
from .models import MessagePlan
from .scenario import ScenarioBuilder


@dataclass(slots=True)
class BomberResult:
    config: dict[str, Any]
    setup_summary: dict[str, Any]
    warmup_metrics: PhaseMetrics | None
    test_metrics: PhaseMetrics


class BomberRunner:
    def __init__(self, config: BomberConfig) -> None:
        self.config = config

    async def run(self) -> BomberResult:
        try:
            import aiohttp
        except ModuleNotFoundError as exc:
            if exc.name == "aiohttp":
                raise RuntimeError(
                    "Missing dependency 'aiohttp'. Install backend requirements before running the bomber."
                ) from exc
            raise

        timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
        connector = aiohttp.TCPConnector(limit=0, ttl_dns_cache=300)

        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            api_client = NyxApiClient(session, self.config.base_url, self.config.headers)
            scenario_builder = ScenarioBuilder(self.config, api_client)
            message_plans = await scenario_builder.build()

            setup_summary = {
                "users": self.config.user_count,
                "conversations": len({plan.conversation_id for plan in message_plans}),
                "message_plans": len(message_plans),
                "target_endpoint": f"{self.config.base_url}{self.config.message_path}",
            }

            warmup_metrics = None
            if self.config.warmup_requests > 0:
                warmup_metrics = await self._run_phase(
                    api_client=api_client,
                    message_plans=message_plans,
                    phase_name="warmup",
                    total_requests=self.config.warmup_requests,
                    show_progress=False,
                )

            test_metrics = await self._run_phase(
                api_client=api_client,
                message_plans=message_plans,
                phase_name="main",
                total_requests=self.config.total_requests,
                show_progress=True,
            )

        return BomberResult(
            config=dump_config(self.config),
            setup_summary=setup_summary,
            warmup_metrics=warmup_metrics,
            test_metrics=test_metrics,
        )

    async def _run_phase(
        self,
        *,
        api_client: NyxApiClient,
        message_plans: list[MessagePlan],
        phase_name: str,
        total_requests: int,
        show_progress: bool,
    ) -> PhaseMetrics:
        metrics = PhaseMetrics(phase_name=phase_name)
        request_counter = count()
        worker_count = min(self.config.concurrency, total_requests)

        metrics.started_at = perf_counter()
        progress_task = None
        if show_progress:
            progress_task = asyncio.create_task(self._progress_reporter(metrics, total_requests))

        try:
            workers = [
                asyncio.create_task(
                    self._worker(
                        api_client=api_client,
                        message_plans=message_plans,
                        metrics=metrics,
                        request_counter=request_counter,
                        total_requests=total_requests,
                    )
                )
                for _ in range(worker_count)
            ]
            await asyncio.gather(*workers)
        finally:
            if progress_task is not None:
                progress_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await progress_task
            metrics.finished_at = perf_counter()

        return metrics

    async def _worker(
        self,
        *,
        api_client: NyxApiClient,
        message_plans: list[MessagePlan],
        metrics: PhaseMetrics,
        request_counter: count,
        total_requests: int,
    ) -> None:
        plan_count = len(message_plans)
        while True:
            request_id = next(request_counter)
            if request_id >= total_requests:
                return
            plan = message_plans[request_id % plan_count]
            await self._send_message(
                api_client=api_client,
                metrics=metrics,
                request_id=request_id,
                plan=plan,
            )

    async def _send_message(
        self,
        *,
        api_client: NyxApiClient,
        metrics: PhaseMetrics,
        request_id: int,
        plan: MessagePlan,
    ) -> None:
        started_at = perf_counter()
        try:
            payload = build_message_payload(
                conversation_id=plan.conversation_id,
                sender_id=str(plan.sender.user_id),
                recipient_id=str(plan.recipient.user_id),
                request_id=request_id,
                message_size_bytes=self.config.message_size_bytes,
            )
            await api_client.post(
                self.config.message_path,
                json_body=payload,
                token=plan.sender.token,
            )
            metrics.record_success((perf_counter() - started_at) * 1000.0)
        except ApiError as exc:
            metrics.record_failure(
                request_id=request_id,
                latency_ms=(perf_counter() - started_at) * 1000.0,
                status_code=exc.status_code,
                error=str(exc),
                context={
                    "conversation_id": plan.conversation_id,
                    "sender": plan.sender.username,
                    "recipient": plan.recipient.username,
                },
            )
        except Exception as exc:
            metrics.record_failure(
                request_id=request_id,
                latency_ms=(perf_counter() - started_at) * 1000.0,
                error=f"{type(exc).__name__}: {exc}",
                context={
                    "conversation_id": plan.conversation_id,
                    "sender": plan.sender.username,
                    "recipient": plan.recipient.username,
                },
            )

    async def _progress_reporter(self, metrics: PhaseMetrics, total_requests: int) -> None:
        while True:
            await asyncio.sleep(self.config.progress_interval_seconds)
            completed = metrics.total_requests
            elapsed = max(perf_counter() - metrics.started_at, 1e-9)
            throughput = completed / elapsed
            print(
                f"[progress] completed={completed}/{total_requests} "
                f"success={metrics.successes} failures={metrics.failures} "
                f"throughput={throughput:.2f} req/s",
                flush=True,
            )
