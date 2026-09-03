from typing import List, Callable, Dict, Any
from src.models.transaction import StandardTransaction
from src.data_collection.providers.base import DataProvider


# 降维成纯粹的调度器，负责连接Provider和Normalizer
class ChainListener:
    """
    数据流调度器 (Orchestrator)。
    统筹底层数据源获取与数据清洗，对外输出标准的 StandardTransaction 对象列表。
    """
    def __init__(self, provider: DataProvider, normalizer_func: Callable[[List[Dict[str, Any]]], List[StandardTransaction]]):   
        """
        初始化调度器。
        
        参数:
            provider (DataProvider): 遵循 DataProvider 接口的具体实现实例（如 EtherscanProvider）
            normalizer_func (Callable): 对应数据源的标准化清洗函数（如 DataNormalizer.normalize_etherscan）
        """

        self.provider = provider
        self.normalizer_func = normalizer_func

    def get_transactions(self, address: str, **kwargs) -> List[StandardTransaction]:
        """
        核心调度流：获取原始数据 -> 清洗 -> 输出标准结构
        参数:
            address (str): 目标区块链地址
            **kwargs: 透传给 Provider 的扩展查询参数
        """

        print(f"[ChainListener]开始调度获取地址{address} 的交易数据:")

        query_kwargs = kwargs.copy()

        # 1 调用数据源获取原始数据
        eth_txs = self.provider.fetch_transactions(address, tx_type="txlist", **query_kwargs)
        token_txs = self.provider.fetch_transactions(address, tx_type="tokentx", **query_kwargs)

        raw_data = eth_txs + token_txs

        if not raw_data:
            print(f"[ChainListener]未从目标地址 {address} 提取到有效数据")
            return []
        
        # 2 调用Normalizer进行数据清洗与转换
        standard_txs = self.normalizer_func(raw_data)
        print(f"[ChainListener]数据处理完成，已生成 {len(standard_txs)} 条标准化交易记录")
        return standard_txs





 
