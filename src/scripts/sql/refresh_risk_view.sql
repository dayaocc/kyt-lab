
-- 模块8：创建视图 —— 每日高风险交易大盘,采用物化视图，定期手动更新
CREATE MATERIALIZED VIEW high_risk_snapshot AS  --CREATE 语句只能运行一次，而 REFRESH 在 while 循环中要运行无数次。
WITH scored_tx AS (
    SELECT
        r.tx_hash,
        r.value,
        (
            CASE WHEN s.entity_type = 'Hacker' THEN 60 ELSE 0 END +
            CASE WHEN r.value > 100 THEN 20 ELSE 0 END +
            CASE WHEN rec.entity_type = 'Mixer' THEN 20 ELSE 0 END
        ) AS total_risk_score
    FROM risk_alerts r
    JOIN address_labels s ON r.from_addr = s.address
    JOIN address_labels rec ON r.to_addr = rec.address
)
SELECT * FROM scored_tx
WHERE total_risk_score >= 80;
-- 必须先给物化视图建立一个“唯一索引”，才能使用并发刷新
CREATE UNIQUE INDEX idx_tx_hash ON high_risk_snapshot (tx_hash);
-- 手动刷新物化视图
REFRESH MATERIALIZED VIEW high_risk_snapshot;