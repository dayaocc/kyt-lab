from abc import ABC, abstractmethod
from typing import List, Dict, Any


class DataProvider(ABC):
    """
    数据源抽象基类。
    定义所有具体数据源（如 Etherscan API、RPC 节点、本地 Mock 数据）必须遵循的系统契约。
    """
    @abstractmethod
    def fetch_transactions(self, address: str, **kwargs) -> List[Dict[str, Any]]:
        """
        获取指定地址的原始交易数据。

        参数:
            address (str): 需要查询的目标区块链地址。
            **kwargs: 扩展参数。用于满足不同底层数据源的特定查询需求
                      (例如: RPC 节点需要的 start_block/end_block，或 Etherscan 需要的 tx_type)。

        返回:
            List[Dict[str, Any]]: 包含原始交易记录的字典列表。数据格式由底层源决定，只做数据搬运，
                                  后续将由 Normalizer 统一清洗。
        """
        pass