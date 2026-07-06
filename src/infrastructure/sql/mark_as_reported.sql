UPDATE risk_alerts
SET is_reported = TRUE
WHERE tx_hash = %s;     -- 这里的 %s 是一个占位符，用于在执行 SQL 时传入具体的交易哈希值。防止 SQL 注入攻击。
--SQL 语句中不确定的部分（如 %s）。因为每笔触发预警的交易哈希都不同，我们不能把哈希值死记硬背在 SQL 里。
-- 需要在执行 SQL 时动态传入具体的哈希值。