from dataclass import dataclass

@dataclass
class Transaction:
    from_addr: str
    to_addr: str
    type: str
    amount: float
    timestamp: str
    symbol: str

return Transaction(
    from_addr=from_addr,
    to_addr=to_addr,
    type=type,
    amount=amount,
    timestamp=timestamp,
    symbol=symbol
)