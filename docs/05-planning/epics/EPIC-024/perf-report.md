# EPIC-024 Performance Report

- Generated at (UTC): `2026-02-10T10:49:35.705662+00:00`
- Iterations per query: `200`
- Synthetic dataset: bookings=`672`, availability_blocks=`40`, synthetic_client_user_id=`15`

## App-level latency summary

| Query | p50 (ms) | p95 (ms) | max (ms) |
|---|---:|---:|---:|
| Availability: active bookings in day window by master | 0.38 | 0.69 | 4.91 |
| Availability: blocks in day window by master | 0.31 | 0.56 | 1.40 |
| Booking create guard: client active future booking exists | 0.30 | 0.41 | 1.50 |
| Master cancel/menu: future active bookings by master | 0.35 | 0.53 | 1.51 |

## EXPLAIN ANALYZE

### Availability: active bookings in day window by master

```sql
SELECT slot_start, slot_end
                FROM bookings
                WHERE master_id = :master_id
                  AND status = 'active'
                  AND slot_end > :day_start
                  AND slot_start < :day_end
                ORDER BY slot_start
```

```text
Index Only Scan using ix_bookings_active_master_slot_window on bookings  (cost=0.25..8.27 rows=1 width=16) (actual time=0.008..0.012 rows=43 loops=1)
  Index Cond: ((master_id = 1) AND (slot_start < '2026-02-20 23:59:59+00'::timestamp with time zone) AND (slot_end > '2026-02-20 00:00:00+00'::timestamp with time zone))
  Heap Fetches: 43
  Buffers: shared hit=4
Planning:
  Buffers: shared hit=35
Planning Time: 0.135 ms
Execution Time: 0.020 ms
```

### Availability: blocks in day window by master

```sql
SELECT start_at, end_at
                FROM availability_blocks
                WHERE master_id = :master_id
                  AND end_at > :day_start
                  AND start_at < :day_end
                ORDER BY start_at
```

```text
Sort  (cost=1.01..1.01 rows=1 width=16) (actual time=0.047..0.047 rows=2 loops=1)
  Sort Key: start_at
  Sort Method: quicksort  Memory: 25kB
  Buffers: shared hit=4
  ->  Seq Scan on availability_blocks  (cost=0.00..1.00 rows=1 width=16) (actual time=0.013..0.015 rows=2 loops=1)
        Filter: ((end_at > '2026-02-20 00:00:00+00'::timestamp with time zone) AND (start_at < '2026-02-20 23:59:59+00'::timestamp with time zone) AND (master_id = 1))
        Rows Removed by Filter: 38
        Buffers: shared hit=1
Planning:
  Buffers: shared hit=6
Planning Time: 0.083 ms
Execution Time: 0.056 ms
```

### Booking create guard: client active future booking exists

```sql
SELECT 1
                FROM bookings
                WHERE client_user_id = :client_user_id
                  AND status = 'active'
                  AND slot_start > :now_at
                LIMIT 1
```

```text
Limit  (cost=0.25..8.27 rows=1 width=4) (actual time=0.023..0.024 rows=1 loops=1)
  Buffers: shared hit=3
  ->  Index Scan using ix_bookings_active_master_slot_window on bookings  (cost=0.25..8.27 rows=1 width=4) (actual time=0.023..0.023 rows=1 loops=1)
        Index Cond: (slot_start > '2026-02-20 00:00:00+00'::timestamp with time zone)
        Filter: (client_user_id = 15)
        Buffers: shared hit=3
Planning Time: 0.045 ms
Execution Time: 0.043 ms
```

### Master cancel/menu: future active bookings by master

```sql
SELECT id, slot_start, service_type
                FROM bookings
                WHERE master_id = :master_id
                  AND status = 'active'
                  AND slot_start >= :now_at
                ORDER BY slot_start
                LIMIT 20
```

```text
Limit  (cost=0.25..8.27 rows=1 width=23) (actual time=0.010..0.012 rows=20 loops=1)
  Buffers: shared hit=3
  ->  Index Scan using ix_bookings_active_master_slot_window on bookings  (cost=0.25..8.27 rows=1 width=23) (actual time=0.009..0.011 rows=20 loops=1)
        Index Cond: ((master_id = 1) AND (slot_start >= '2026-02-20 00:00:00+00'::timestamp with time zone))
        Buffers: shared hit=3
Planning:
  Buffers: shared hit=9
Planning Time: 0.111 ms
Execution Time: 0.023 ms
```
