from dataclasses import dataclass

@dataclass
class StandardTransaction:
    """
    KYT 系统的标准交易数据模型 (Data Contract)。
    所有外部数据源的原始数据，经过 Normalizer 清洗后，都必须转化为该对象，
    供下游的 TraceEngine 和 RiskEngine 使用。
    """
    tx_hash: str
    from_address: str
    to_address: str
    amount: float
    timestamp: int
    token_symbol: str = "UNKNOWN"
    is_success: bool = True
    error_msg: str = ""

    def __post_init__(self):
        """
        数据清洗卡口：对象初始化后自动执行。
        强制将地址和哈希转换为小写，从源头杜绝大小写匹配导致的数据断层。
        """
        self.from_address = self.from_address.lower() if self.from_address else ""
        self.to_address = self.to_address.lower() if self.to_address else ""
        self.tx_hash = self.tx_hash.lower() if self.tx_hash else ""

    def to_dict(self):
        """
        定义一个对象方法，方便在某些需要字典格式的地方（如 JSON 序列化）调用
        """
        return {
            "tx_hash": self.tx_hash,
            "from_address": self.from_address,
            "to_address": self.to_address,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "token_symbol": self.token_symbol,
            "is_success": self.is_success,
            "error_msg": self.error_msg
        }