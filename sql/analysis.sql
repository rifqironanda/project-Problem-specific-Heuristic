-- PostgreSQL queries. Schema is created by SQLAlchemy on startup.
SELECT dataset_id, asset, COUNT(*) AS observations,
       AVG(value) AS mean_daily_return, STDDEV_POP(value)*SQRT(252) AS annual_volatility
FROM daily_returns GROUP BY dataset_id, asset ORDER BY dataset_id, asset;

SELECT run_id, method, SUM(weight) AS total_weight, MAX(weight) AS largest_weight
FROM allocations GROUP BY run_id, method ORDER BY run_id, method;

SELECT id, report::jsonb->>'dataset_sha256' AS dataset_sha256,
       report::jsonb->>'target_annual_return' AS target
FROM experiment_runs ORDER BY created_at DESC;

SELECT r.id, item->>'method' AS method, item->>'feasible' AS feasible,
       (item->>'variance')::double precision AS variance
FROM experiment_runs r CROSS JOIN LATERAL jsonb_array_elements(r.report::jsonb->'results') AS item;
