SELECT tx_hash, from_addr, to_addr, symbol, value, timestamp
FROM transactions
WHERE from_addr = %s OR to_addr = %s