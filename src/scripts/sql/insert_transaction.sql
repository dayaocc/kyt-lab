INSERT INTO transactions (   --往 transactions 表 插入数据,并指定插入的列
    tx_hash,
    from_addr,
    to_addr,
    value,      --在 Python 将数据交给 PostgreSQL 时，数据库是不看字典的键名的。它只认顺序
    input_data,
    block_number,
    timestamp,
    tx_type,
    token_address,
    symbol
)
VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (tx_hash)
DO NOTHING;   -- 遇到重复数据时，采用“什么都不做”