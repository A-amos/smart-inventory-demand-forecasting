# Actual prototype performance measurements

Executed 2026-10-01 against local Docker Desktop/WSL2, MySQL8.4.11, FastAPI and frozen historical inference. Windows11 build26300, HP EliteBook840G5, eight logical processors, approximately15.85GiB installed RAM; native Python3.12.14/httpx client. Measurement uses `perf_counter`, `ThreadPoolExecutor` and NumPy percentiles. Raw statuses and per-request timings: [phase6-performance.json](phase6-performance.json); executable [script](../../scripts/phase6_performance.py).

Normal: one worker × eight requests ×11 operations =88. Modest concurrent: four workers × eight ×11 =352. Total **440 measured requests, zero errors** after the verified fix. Four simulated concurrent workers share one authorized manager identity; each has its own product for writes. This is not four recruited users. Requests are closed-loop per operation, not a sustained mixed retail arrival model. Setup, one actual28-day inference warmup per worker, prerequisite stock GETs and cleanup are outside individual request samples. Total run including setup/cleanup: **246.120s**. Each result duration is the operation group's wall time. Round trips include HTTP/server/database work; no browser rendering time is inferred.

| Mode | Operation | Workers | Requests | Mean ms | p50 ms | p95 ms | Max ms | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| normal | liveness | 1 | 8 | 7.76 | 7.85 | 8.59 | 8.77 | 0 |
| normal | readiness | 1 | 8 | 11.23 | 10.17 | 14.25 | 14.71 | 0 |
| normal | login | 1 | 8 | 201.18 | 194.05 | 245.49 | 259.87 | 0 |
| normal | products | 1 | 8 | 23.91 | 23.72 | 25.11 | 25.40 | 0 |
| normal | sales | 1 | 8 | 28.01 | 26.65 | 33.53 | 35.57 | 0 |
| normal | inventory_update | 1 | 8 | 38.26 | 37.21 | 50.67 | 55.68 | 0 |
| normal | operational_sale | 1 | 8 | 41.76 | 42.95 | 46.25 | 46.48 | 0 |
| normal | forecast_retrieval | 1 | 8 | 30.62 | 29.65 | 36.38 | 39.05 | 0 |
| normal | forecast_inference | 1 | 8 | 4658.39 | 3097.74 | 12363.41 | 14250.99 | 0 |
| normal | recommendation | 1 | 8 | 4349.09 | 3714.74 | 8464.31 | 8994.98 | 0 |
| normal | dashboard | 1 | 8 | 293.18 | 250.60 | 467.17 | 469.35 | 0 |
| modest_concurrent | liveness | 4 | 32 | 224.14 | 29.05 | 1293.50 | 2707.31 | 0 |
| modest_concurrent | readiness | 4 | 32 | 193.93 | 105.53 | 299.76 | 2403.50 | 0 |
| modest_concurrent | login | 4 | 32 | 2893.21 | 3000.40 | 3869.20 | 3970.91 | 0 |
| modest_concurrent | products | 4 | 32 | 257.65 | 256.46 | 456.54 | 514.24 | 0 |
| modest_concurrent | sales | 4 | 32 | 386.86 | 385.16 | 564.18 | 573.60 | 0 |
| modest_concurrent | inventory_update | 4 | 32 | 479.90 | 429.62 | 878.30 | 999.89 | 0 |
| modest_concurrent | operational_sale | 4 | 32 | 534.51 | 496.68 | 845.82 | 886.80 | 0 |
| modest_concurrent | forecast_retrieval | 4 | 32 | 436.86 | 435.52 | 687.22 | 741.46 | 0 |
| modest_concurrent | forecast_inference | 4 | 32 | 10775.52 | 10191.52 | 16823.98 | 16925.73 | 0 |
| modest_concurrent | recommendation | 4 | 32 | 691.97 | 698.31 | 754.18 | 795.66 | 0 |
| modest_concurrent | dashboard | 4 | 32 | 431.49 | 430.86 | 480.55 | 522.45 | 0 |


Inventory integrity was checked after both workload modes: worker0 stock1000→984 after eight normal sales plus eight concurrent sales; workers1–3 stock1000→992 after eight concurrent sales each. Inventory-update measurements preserve on-hand and increment the audit/version; they do not consume stock. Raw report contains stock and sale-count assertions. Actual same-stock competing-sale verification is separately [43 live checks](phase6-sales-live.json): one201 and one409, one decrement/audit. Worker-specific stress stock alone would not prove same-row integrity.

First run had **four sale HTTP503 responses** under four workers. [Original failure](phase6-performance-first-failure.json) and [InnoDB diagnostic](phase6-innodb-diagnostic.txt) are preserved. InnoDB identified unique-request-key gap-lock deadlocks across different products. A bounded transaction retry now retries only MySQL1213, up to three total attempts, after rollback, with10/20ms backoff. It rechecks stock/version and uses the same UUID. Exhaustion and other database errors remain explicit503; stale/insufficient stock remain409. Three regression cases prove rollback/one-sale success, exhaustion and no retry on connection errors. [Official MySQL deadlock handling](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlocks-handling.html) supports retrying victim transactions. The second full440-request run passed.

Concurrent inference p95 was approximately16.824s and login p95 approximately3.869s: these are material prototype delays, not hidden failures. CPU-heavy hashing/inference and shared-machine contention contribute; this test does not isolate their causal shares. Eight samples per normal operation and32 concurrent samples make tail estimates unstable. The proposal supplies no numerical SLA, so no invented latency threshold is marked passed. No commercial-scale capacity, throughput maximum, long-duration reliability or enterprise SLA is established. Research inference is the acknowledged2011 UK scenario; current2026 forecasts remain unavailable.
