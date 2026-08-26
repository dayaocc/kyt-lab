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

        # 1 调用数据源获取原始数据
        raw_data = self.provider.fetch_transactions(address, **kwargs)
        if not raw_data:
            print(f"[ChainListener]未从目标地址 {address} 提取到有效数据")
            return []
        
        # 2 调用Normalizer进行数据清洗与转换
        standard_txs = self.normalizer_func(raw_data)
        print(f"[CahinListener]数据处理完成，已生成 {len(standard_txs)} 条标准化交易记录")
        return standard_txs





 
        
"""
if __name__ == "__main__":
    print("正在启动KYT数据采集引擎...")
    # 先实例化一个DatabaseManager数据库管理器对象，建立数据库连接
    db = DatabaseManager(DB_CONFIG)
    db.create_tables()   # 确保数据表结构已经就绪，如果表已经存在，create_tables 方法会自动跳过，不会报错
    # # 再实例化一个 ChainListener 对象，并把 db 对象作为参数塞进去
    listener = ChainListener(db_manager=db)

    test_tx_hash = "0xfc6567db30fd74b27a6d158a0c4852b8faddae02579f529792272633e10ba125"

    print(f"正在解析交易：{test_tx_hash}")

    # 解析交易
    tx_data = listener.decode_transaction(test_tx_hash)

    tx_data['tx_hash'] = test_tx_hash
  
     
    # 判断并入库
    if tx_data.get("type") != "ERROR" and tx_data.get("type") != "DECODE_FAILED":
        print(f"解码成功: {tx_data.get('symbol')} 转账 {tx_data.get('amount')}")

        # 写入数据库
        # 访问 ChainListener 对象的 db 属性（即之前传入的 DatabaseManager 实例），调用它(db)的 insert_transaction 方法，把解析后的交易数据 tx_data 传进去。
        # 写入数据库，并获取返回的成功与否状态
        is_success = listener.db.insert_transaction(tx_data)

        if is_success:            
            # 提交事务（如果是批量处理，这个commit 应该放在循环外面）
            listener.db.commit()
            print("数据已永久写入PostgreSQL 数据库!")
        else:
            print("数据写入失败，已回滚当前事务。")
    else:
        print(f"交易解析失败或跳过，原因：{tx_data}")

    # 关闭数据库连接
    db.close()
    print("测试结束")


    # print(listener.decode_transaction("0x44f4a5cb42c77494e019c0af6ea77f6a7a7f27c88dddab8a8e76a6875a0077f6"))
    # print(listener.decode_transaction("0xfc6567db30fd74b27a6d158a0c4852b8faddae02579f529792272633e10ba125"))
    
"""

