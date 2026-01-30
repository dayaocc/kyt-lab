CREATE TABLE IF NOT EXISTS risk_alerts (
    tx_hash text,
    from_addr text,
    to_addr text,
    value numeric(20, 6),
    risk_level text,
    rule_name text,
    scanned_at timestamp
);