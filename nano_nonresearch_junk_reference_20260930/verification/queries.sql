-- README가 있는 자료 폴더를 작업 디렉터리로 사용한다.
-- All statements are read-only SELECT queries over the copied snapshot.

-- exclusion_reasons
SELECT reason, count(*) AS documents
FROM read_parquet('data/exclusion_flags.parquet')
GROUP BY reason ORDER BY reason;

-- exclusion_uniqueness
SELECT count(*) AS rows, count(DISTINCT work_id) AS unique_work_ids
FROM read_parquet('data/exclusion_flags.parquet');

-- junk_flags
SELECT flag_source, flag_only, count(*) AS documents
FROM read_parquet('data/junk_doc_flags_v3.parquet')
GROUP BY ALL ORDER BY ALL;

-- nano_ratio_summary
SELECT count(*) AS nanos, sum(members) AS original_members,
       sum(jd) AS nonresearch_documents,
       count(*) FILTER (WHERE pct_mem_jd >= 50) AS nanos_ge50,
       count(*) FILTER (WHERE pct_mem_jd >= 30 AND pct_mem_jd < 50) AS nanos_ge30_lt50,
       count(*) FILTER (WHERE pct_mem_jd >= 30) AS nanos_ge30
FROM read_parquet('data/a5_dist.parquet');

-- mapping_status_summary
SELECT status, count(*) AS nanos
FROM read_parquet('data/mapping_unit_status.parquet')
GROUP BY status ORDER BY status;
