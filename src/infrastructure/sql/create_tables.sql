CREATE TABLE IF NOT EXISTS transactions (
    tx_hash VARCHAR(66) PRIMARY KEY,
    from_addr VARCHAR(42) NOT NULL,
    to_addr VARCHAR(42),
    value NUMERIC NOT NULL,
    input_data TEXT,
    block_number INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    tx_type VARCHAR(20) NOT NULL,
    token_address VARCHAR(42),
    symbol VARCHAR(10)
);