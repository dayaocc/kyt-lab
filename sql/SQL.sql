SELECT tx_hash, value
FROM risk_alerts
WHERE value > 1000 AND risk_level = 'High'
ORDER BY value DESC   --按金额从大到小排序（DESC 代表降序）




-- 模块 2：情报关联 —— 多表画像分析，将“链上数据”和“情报库”关联起来分析
SELECT 
    r.tx_hash,
    r.value,
    r.from_addr,
    l.entity_name 
FROM risk_alerts r
JOIN address_labels l    -- 找两张表的**“共同语言”。address_labels（身份标签表）
ON r.from_addr = l.address     -- “请把r表里的 from_addr 列，去和 l表里的 address 列进行对齐匹配。”
WHERE l.entity_type = 'Hacker';   -- 精准锁定黑客关联交易

-- 模块3：模式识别
SELECT 
    from_addr,
    COUNT(*) AS tx_count,
    SUM(value) AS total_value
FROM risk_alerts
GROUP BY from_addr   --核心：按地址分组


-- 完整的“黑客资产追踪”指令
SELECT          --4.“投影”输出你想看的列。到这一步才决定输出哪些列
    r.tx_hash,
    r.value,
    l.entity_name,
    l.entity_type,
    SUM(r.value) AS total_eth_volume,   -- 统计该类型的总涉案金额
    COUNT(*) AS alert_count         -- 统计该类型的总交易笔数
FROM risk_alerts r  -- 1.拿出risk_alerts整张表
JOIN address_labels l ON r.from_addr = l.address    -- 2.把两张表按地址对齐比较
--WHERE l.entity_type = 'Hacker'      -- 3.过滤掉非黑客地址
GROUP BY l.entity_type;     -- 把所有属于 'Hacker' 的钱分一组
ORDER BY total_eth_volume DESC;   -- 按总金额从大到小排序


-- 模块4：情报库数据补充 —— 插入新的标签数据
CREATE TABLE address_labels (
    address VARCHAR(42),
    entity_name TEXT,
    entity_type VARCHAR(50),
    label_source TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
--往里面存入真实的“情报”数据
INSERT INTO address_labels (address, entity_name, entity_type) VALUES
(
    '0x1234567890abcdef1234567890abcdef12345678', 'Lazarus', 'Hacker'
);


--模块5：数据统计与时间筛选
--风险大盘统计，不同风险等级（High/Medium/Low）各占多少比例，以及涉及的总金额。
SELECT
    risk_level,
    COUNT(*) AS alert_count,
    SUM(value) AS total_value
FROM risk_alerts
GROUP BY risk_level;
-- 添加时效性，过去24小时
WHERE scanned_at >= NOW() - INTERVAL '24 hours'   -- 只看最近24小时的数据

-- 完整的筛选等级，看最新失效的高风险告警
SELECT
    risk_level,
    COUNT(*) AS alert_count,
    SUM(value) AS total_value
FROM risk_alerts
WHERE scanned_at >= NOW() - INTERVAL '24 hours'   
GROUP BY risk_level;
-- 嫌疑人行为分析
SELECT
    from_addr,
    COUNT(*) AS tx_count,
    SUM(value) AS total_value
FROM risk_alerts
WHERE scanned_at >= NOW() - INTERVAL '24 hours'   
GROUP BY from_addr
HAVING COUNT(*) > 10        --tx_count 是 SELECT 阶段才“起的别名”，而 HAVING 执行时它还不存在,所以要用 COUNT(*) 代替
ORDER BY tx_count DESC;

-- 模块6：资金流向透视
--资金流向透视，找出所有从高风险地址流向**交易所（Exchange）**的交易。
SELECT
    r.tx_hash,
    r.from_addr,
    r.to_addr,
    l.entity_name AS receiver_name,     -- 这里的名字是收款方的
    l.entity_type AS receiver_type
FROM risk_alerts r
JOIN address_labels l ON r.to_addr = l.address    --对齐收款方地址
WHERE l.entity_type = 'Exchange'    --目标锁定：交易所
    AND r.risk_level = 'High';      --来源锁定：高风险资金

-- 双重对齐，找出发送方和接收方都包含在内的所有高风险地址之间的交易
SELECT
    r.tx_hash,
    s.entity_name AS sender_name,
    s.entity_type AS receiver_type
FROM risk_alerts r
JOIN address_labels s ON r.from_addr = s.address    --对齐付款方地址
JOIN address_labels rec ON r.to_addr = rec.address      --对齐收款方地址
WHERE s.entity_type = 'Hacker'      --付款方是黑客
    AND rec.entity_type = 'Exchange'    --收款方是交易所

-- 模块6：资金流向透视（完整版）
SELECT
    r.tx_hash,
    r.value AS amount_eth,
    s.entity_name AS sender_hacker_group,
    rec.entity_name AS target_exchange,
    r.scanned_at
FROM risk_alerts r
JOIN address_labels s ON r.from_addr = s.address    --对齐付款方地址
JOIN address_labels rec ON r.to_addr = rec.address      --对齐收款方地址
WHERE s.entity_type = 'Hacker'
    AND rec.entity_type = 'Exchange'
    AND r.risk_level = 'High'
ORDER BY r.value DESC;

-- 模块7：风险评分与自动化建议
-- 1. 先定义“笔记本”内容
WITH scored_tx AS (
SELECT
    r.tx_hash,
    s.entity_type AS sender_type,
    rec.entity_type AS receiver_type,
    -- 计算综合风险评分的逻辑
    (
        CASE
            WHEN s.entity_type = 'Hacker' THEN 60
            ELSE 0
        END +
        CASE
            WHEN r.value > 100 THEN 20
            ELSE 0
        END +
        CASE
            WHEN rec.entity_type = 'Mixer' THEN 20
            ELSE 0
        END
    ) AS total_risk_score
FROM risk_alerts r
JOIN address_labels s ON r.from_addr = s.address
JOIN address_labels rec ON r.to_addr = rec.address
)
ORDER BY total_risk_score DESC     -- 让最危险的交易排在最上面
--- 2. 再从“笔记本”里筛选高分项
SELECT * FROM scored_tx
WHERE total_risk_score >= 80;


-- 模块8：创建视图 —— 每日高风险交易大盘,采用物化视图，定期手动更新
CREATE MATERIALIZED VIEW high_risk_snapshot AS
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