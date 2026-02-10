from __future__ import annotations

import argparse
import statistics
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text

from app.db.session import get_engine

PERF_TAG = "__epic024_perf__"
CLIENT_TG = -910000101
PROFILE_DATE = "2026-02-20"


@dataclass(frozen=True)
class QueryCase:
    key: str
    title: str
    sql: str
    params: dict[str, object]


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile booking/schedule query hotspots (EPIC-024).")
    parser.add_argument(
        "--output",
        default="docs/05-planning/epics/EPIC-024/perf-report.md",
        help="Path for markdown report output.",
    )
    parser.add_argument("--iterations", type=int, default=200, help="Number of app-level timing iterations per query.")
    parser.add_argument("--keep-data", action="store_true", help="Keep synthetic profiling rows after report.")
    args = parser.parse_args()

    cases = _build_cases()
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    engine = get_engine()
    generated_at = datetime.now(UTC)
    with engine.begin() as conn:
        seeded = _seed_profile_data(conn)
        cases = _materialize_cases(_build_cases(), perf_client_user_id=seeded["perf_client_user_id"])
        explain_outputs: dict[str, list[str]] = {}
        app_timings: dict[str, list[float]] = {}
        for case in cases:
            explain_outputs[case.key] = _run_explain(conn, case)
            app_timings[case.key] = _measure_latency(conn, case, iterations=max(1, args.iterations))

        if not args.keep_data:
            _cleanup_profile_data(conn, seeded)

    out_path.write_text(
        _build_markdown_report(
            generated_at=generated_at,
            iterations=max(1, args.iterations),
            seeded=seeded,
            cases=cases,
            explain_outputs=explain_outputs,
            app_timings=app_timings,
        ),
        encoding="utf-8",
    )
    print(f"Report written: {out_path}")


def _build_cases() -> list[QueryCase]:
    return [
        QueryCase(
            key="availability_active_bookings_day",
            title="Availability: active bookings in day window by master",
            sql="""
                SELECT slot_start, slot_end
                FROM bookings
                WHERE master_id = :master_id
                  AND status = 'active'
                  AND slot_end > :day_start
                  AND slot_start < :day_end
                ORDER BY slot_start
            """,
            params={
                "master_id": 1,
                "day_start": f"{PROFILE_DATE}T00:00:00+00:00",
                "day_end": f"{PROFILE_DATE}T23:59:59+00:00",
            },
        ),
        QueryCase(
            key="availability_blocks_day",
            title="Availability: blocks in day window by master",
            sql="""
                SELECT start_at, end_at
                FROM availability_blocks
                WHERE master_id = :master_id
                  AND end_at > :day_start
                  AND start_at < :day_end
                ORDER BY start_at
            """,
            params={
                "master_id": 1,
                "day_start": f"{PROFILE_DATE}T00:00:00+00:00",
                "day_end": f"{PROFILE_DATE}T23:59:59+00:00",
            },
        ),
        QueryCase(
            key="client_future_active_exists",
            title="Booking create guard: client active future booking exists",
            sql="""
                SELECT 1
                FROM bookings
                WHERE client_user_id = :client_user_id
                  AND status = 'active'
                  AND slot_start > :now_at
                LIMIT 1
            """,
            params={
                "client_user_id": None,
                "now_at": f"{PROFILE_DATE}T00:00:00+00:00",
            },
        ),
        QueryCase(
            key="master_future_active_list",
            title="Master cancel/menu: future active bookings by master",
            sql="""
                SELECT id, slot_start, service_type
                FROM bookings
                WHERE master_id = :master_id
                  AND status = 'active'
                  AND slot_start >= :now_at
                ORDER BY slot_start
                LIMIT 20
            """,
            params={
                "master_id": 1,
                "now_at": f"{PROFILE_DATE}T00:00:00+00:00",
            },
        ),
    ]


def _materialize_cases(cases: list[QueryCase], *, perf_client_user_id: int) -> list[QueryCase]:
    materialized: list[QueryCase] = []
    for case in cases:
        params = dict(case.params)
        if case.key == "client_future_active_exists":
            params["client_user_id"] = perf_client_user_id
        materialized.append(QueryCase(key=case.key, title=case.title, sql=case.sql, params=params))
    return materialized


def _seed_profile_data(conn) -> dict[str, int]:
    conn.execute(text("DELETE FROM availability_blocks WHERE reason = :perf_tag"), {"perf_tag": PERF_TAG})
    conn.execute(text("DELETE FROM bookings WHERE manual_client_name = :perf_tag"), {"perf_tag": PERF_TAG})

    role_id = conn.execute(text("SELECT id FROM roles WHERE name = 'Client'")).scalar_one()
    conn.execute(
        text(
            """
            INSERT INTO users (telegram_user_id, telegram_username, role_id)
            VALUES (:telegram_user_id, :telegram_username, :role_id)
            ON CONFLICT (telegram_user_id) DO UPDATE
            SET telegram_username = excluded.telegram_username
            """
        ),
        {"telegram_user_id": CLIENT_TG, "telegram_username": PERF_TAG, "role_id": int(role_id)},
    )
    perf_client_id = int(
        conn.execute(text("SELECT id FROM users WHERE telegram_user_id = :telegram_user_id"), {"telegram_user_id": CLIENT_TG}).scalar_one()
    )
    # 14 days * 48 slots/day = 672 synthetic rows.
    inserted_bookings = int(
        conn.execute(
            text(
                """
                INSERT INTO bookings (
                    master_id,
                    client_user_id,
                    service_type,
                    slot_start,
                    slot_end,
                    status,
                    manual_client_name
                )
                SELECT
                    1,
                    :client_user_id,
                    CASE WHEN (g.n % 3) = 0 THEN 'haircut_beard' ELSE 'haircut' END,
                    (:start_base)::timestamptz + (g.n * interval '30 minute'),
                    (:start_base)::timestamptz + ((g.n + 1) * interval '30 minute'),
                    CASE WHEN (g.n % 11) = 0 THEN 'completed' ELSE 'active' END,
                    :perf_tag
                FROM generate_series(0, 671) AS g(n)
                """
            ),
            {
                "client_user_id": perf_client_id,
                "start_base": f"{PROFILE_DATE}T00:00:00+00:00",
                "perf_tag": PERF_TAG,
            },
        ).rowcount
        or 0
    )
    inserted_blocks = int(
        conn.execute(
            text(
                """
                INSERT INTO availability_blocks (master_id, block_type, start_at, end_at, reason)
                SELECT
                    1,
                    CASE WHEN (g.n % 2) = 0 THEN 'day_off' ELSE 'manual_block' END,
                    (:start_base)::timestamptz + (g.n * interval '12 hour'),
                    (:start_base)::timestamptz + (g.n * interval '12 hour') + interval '2 hour',
                    :perf_tag
                FROM generate_series(0, 39) AS g(n)
                """
            ),
            {"start_base": f"{PROFILE_DATE}T00:00:00+00:00", "perf_tag": PERF_TAG},
        ).rowcount
        or 0
    )
    return {
        "perf_client_user_id": perf_client_id,
        "inserted_bookings": inserted_bookings,
        "inserted_blocks": inserted_blocks,
    }


def _cleanup_profile_data(conn, seeded: dict[str, int]) -> None:
    conn.execute(text("DELETE FROM availability_blocks WHERE reason = :perf_tag"), {"perf_tag": PERF_TAG})
    conn.execute(text("DELETE FROM bookings WHERE manual_client_name = :perf_tag"), {"perf_tag": PERF_TAG})
    conn.execute(text("DELETE FROM users WHERE id = :id"), {"id": seeded["perf_client_user_id"]})


def _run_explain(conn, case: QueryCase) -> list[str]:
    rows = conn.execute(text(f"EXPLAIN (ANALYZE, BUFFERS) {case.sql}"), case.params).all()
    return [str(row[0]) for row in rows]


def _measure_latency(conn, case: QueryCase, *, iterations: int) -> list[float]:
    elapsed_ms: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        conn.execute(text(case.sql), case.params).fetchall()
        elapsed_ms.append((time.perf_counter() - start) * 1000.0)
    return elapsed_ms


def _build_markdown_report(
    *,
    generated_at: datetime,
    iterations: int,
    seeded: dict[str, int],
    cases: list[QueryCase],
    explain_outputs: dict[str, list[str]],
    app_timings: dict[str, list[float]],
) -> str:
    lines: list[str] = []
    lines.append("# EPIC-024 Performance Report")
    lines.append("")
    lines.append(f"- Generated at (UTC): `{generated_at.isoformat()}`")
    lines.append(f"- Iterations per query: `{iterations}`")
    lines.append(
        "- Synthetic dataset:"
        f" bookings=`{seeded['inserted_bookings']}`,"
        f" availability_blocks=`{seeded['inserted_blocks']}`,"
        f" synthetic_client_user_id=`{seeded['perf_client_user_id']}`"
    )
    lines.append("")
    lines.append("## App-level latency summary")
    lines.append("")
    lines.append("| Query | p50 (ms) | p95 (ms) | max (ms) |")
    lines.append("|---|---:|---:|---:|")
    for case in cases:
        values = app_timings[case.key]
        p50 = _percentile(values, 50)
        p95 = _percentile(values, 95)
        lines.append(f"| {case.title} | {p50:.2f} | {p95:.2f} | {max(values):.2f} |")
    lines.append("")
    lines.append("## EXPLAIN ANALYZE")
    lines.append("")
    for case in cases:
        lines.append(f"### {case.title}")
        lines.append("")
        lines.append("```sql")
        lines.append(case.sql.strip())
        lines.append("```")
        lines.append("")
        lines.append("```text")
        lines.extend(explain_outputs[case.key])
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def _percentile(values: list[float], pct: int) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    try:
        return statistics.quantiles(values, n=100)[pct - 1]
    except Exception:
        ordered = sorted(values)
        idx = max(0, min(len(ordered) - 1, int(round((pct / 100) * (len(ordered) - 1)))))
        return ordered[idx]


if __name__ == "__main__":
    main()
