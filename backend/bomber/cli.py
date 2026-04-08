from __future__ import annotations

import argparse
import asyncio
import sys

from .config import BomberConfig
from .metrics import export_failure_log, export_json_report, render_report
from .runner import BomberRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Nyx bomber: realistic multi-user load test for the /messages endpoint."
    )
    parser.add_argument("--base-url", required=True, help="Base HTTP API URL, for example https://host/main")
    parser.add_argument("--requests", dest="total_requests", type=int, default=100_000)
    parser.add_argument("--concurrency", type=int, default=1_000)
    parser.add_argument("--users", dest="user_count", type=int, default=100)
    parser.add_argument("--timeout", dest="timeout_seconds", type=float, default=10.0)
    parser.add_argument("--warmup", dest="warmup_requests", type=int, default=0)
    parser.add_argument(
        "--progress-interval",
        dest="progress_interval_seconds",
        type=float,
        default=1.0,
    )
    parser.add_argument("--username-prefix", default="bomber-user")
    parser.add_argument("--master-password-prefix", default="bomber-master")
    parser.add_argument("--message-size", dest="message_size_bytes", type=int, default=96)
    parser.add_argument(
        "--users-file",
        dest="users_file",
        help="Path to a JSON file with pre-created users [{\"username\":...,\"master_password\":...}]",
    )
    parser.add_argument(
        "--skip-register",
        dest="register_missing_users",
        action="store_false",
        help="Do not register synthetic users before login.",
    )
    parser.add_argument(
        "-H",
        "--header",
        dest="headers",
        action="append",
        help="Optional header in the form 'Key: Value'.",
    )
    parser.add_argument("--export-json", dest="export_json_path")
    parser.add_argument("--failure-log", dest="failure_log_path")
    return parser


async def run_from_args(args: argparse.Namespace) -> int:
    config = BomberConfig.from_cli(
        base_url=args.base_url,
        total_requests=args.total_requests,
        concurrency=args.concurrency,
        timeout_seconds=args.timeout_seconds,
        warmup_requests=args.warmup_requests,
        progress_interval_seconds=args.progress_interval_seconds,
        user_count=args.user_count,
        username_prefix=args.username_prefix,
        master_password_prefix=args.master_password_prefix,
        register_missing_users=args.register_missing_users,
        message_size_bytes=args.message_size_bytes,
        headers=args.headers,
        users_file=args.users_file,
        export_json_path=args.export_json_path,
        failure_log_path=args.failure_log_path,
    )

    print(
        f"Preparing scenario with {config.user_count} users targeting {config.base_url}{config.message_path}",
        flush=True,
    )
    runner = BomberRunner(config)
    result = await runner.run()

    print()
    print("Scenario Setup")
    print(f"Users: {result.setup_summary['users']}")
    print(f"Conversations: {result.setup_summary['conversations']}")
    print(f"Message Plans: {result.setup_summary['message_plans']}")
    print(f"Target Endpoint: {result.setup_summary['target_endpoint']}")

    if result.warmup_metrics is not None:
        print()
        print(render_report(result.warmup_metrics))

    print()
    print(render_report(result.test_metrics))

    if config.failure_log_path is not None:
        export_failure_log(config.failure_log_path, result.test_metrics.failure_records)
        print(f"\nFailure log exported to: {config.failure_log_path}")

    if config.export_json_path is not None:
        export_json_report(
            config.export_json_path,
            {
                "config": result.config,
                "setup": result.setup_summary,
                "warmup": result.warmup_metrics.to_dict() if result.warmup_metrics else None,
                "test": result.test_metrics.to_dict(),
            },
        )
        print(f"JSON report exported to: {config.export_json_path}")

    return 0 if result.test_metrics.failures == 0 else 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return asyncio.run(run_from_args(args))
    except KeyboardInterrupt:
        print("\nBomber interrupted by user.", file=sys.stderr)
        return 130
    except ValueError as exc:
        parser.error(str(exc))
        return 2
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
