import duckdb
con = duckdb.connect(); con.execute("SET threads=64")
M="/home/snoopy/Positron/nano-cluster-massage/resource/thk_ver/coreset_papers_with_meta.parquet"
q=lambda s: con.execute(s).fetchdf()
print("-- nano 51894 titles rank 11-40:")
print(q(f"SELECT coreset_rank, publication_year, cited_by_count, substr(title,1,110) t FROM '{M}' WHERE nano_id=51894 AND coreset_rank BETWEEN 11 AND 40 ORDER BY coreset_rank").to_string())
print("-- nano 51894: how many of 65 titles contain '$$' or '\\':", q(f"SELECT sum(title LIKE '%$$%' OR title LIKE '%\\\\%') latex, count(*) FROM '{M}' WHERE nano_id=51894").to_string())
print("-- nano 51894 titles matching spinor/immersion:", q(f"SELECT coreset_rank, substr(title,1,120) FROM '{M}' WHERE nano_id=51894 AND (title ILIKE '%spinor%' OR title ILIKE '%immersion%' OR title ILIKE '%submanifold%') ORDER BY coreset_rank").to_string())
print("-- nano 41609 titles rank 11-30:")
print(q(f"SELECT coreset_rank, publication_year, cited_by_count, substr(title,1,110) t FROM '{M}' WHERE nano_id=41609 AND coreset_rank BETWEEN 11 AND 30 ORDER BY coreset_rank").to_string())
print("-- nano 41609: 'Correction' count of 30:", q(f"SELECT sum(title ILIKE 'correction%') corr, count(*) FROM '{M}' WHERE nano_id=41609").to_string())
# global: junk-title dominance per nano
print("-- global junk-title share per nano (coreset titles matching junk regex):")
con.execute(f"""CREATE TABLE junk AS SELECT nano_id, count(*) n, 
  sum(CASE WHEN regexp_matches(title, '^(?i)\\s*(correction|corrigend|errat|editorial|preface|foreword|introduction$|book review|reply|response to|letter to the editor|author index|subject index|untitled|abstracts?$|front matter|back matter|table of contents|issue information|announcement|obituary|in memoriam|acknowledg|masthead|contents|title page|list of|index$)') THEN 1 ELSE 0 END) junk_n,
  sum(CASE WHEN title LIKE '%$$%' OR title LIKE '%\\\\%' THEN 1 ELSE 0 END) latex_n
  FROM '{M}' GROUP BY 1""")
print(q("SELECT sum(junk_n>=n*0.5) nanos_junk_ge50, sum(junk_n>=n*0.3) ge30, sum(junk_n>=n*0.1) ge10, sum(latex_n>=n*0.5) latex_ge50, sum(latex_n>=n*0.3) latex_ge30, count(*) FROM junk").to_string())
print(q("SELECT j.nano_id, j.n, j.junk_n, j.latex_n, l.label_en, l.confidence, l.needs_review FROM junk j JOIN 'lab_joined.parquet' l USING(nano_id) WHERE junk_n>=n*0.3 OR latex_n>=n*0.3 ORDER BY greatest(junk_n,latex_n)*1.0/n DESC LIMIT 30").to_string())
con.execute("COPY junk TO 'junk_share.parquet'")
# top-10 only junk share
con.execute(f"""CREATE TABLE junk10 AS SELECT nano_id, sum(CASE WHEN regexp_matches(title, '^(?i)\\s*(correction|corrigend|errat|editorial|preface|foreword|introduction$|book review|reply|response to|letter to the editor|author index|subject index|untitled|abstracts?$|front matter|issue information|obituary|in memoriam)') THEN 1 ELSE 0 END) junk10 FROM '{M}' WHERE coreset_rank<=10 GROUP BY 1""")
print(q("SELECT junk10, count(*) FROM junk10 GROUP BY 1 ORDER BY 1").to_string())
# correlation: confidence for nanos with junk10>=5
print(q("SELECT CASE WHEN junk10>=5 THEN 'junk10>=5' WHEN junk10>=1 THEN 'junk10 1-4' ELSE 'clean' END g, count(*), round(avg(l.confidence),3), sum(l.needs_review) FROM junk10 j JOIN 'lab_joined.parquet' l USING(nano_id) GROUP BY 1").to_string())
