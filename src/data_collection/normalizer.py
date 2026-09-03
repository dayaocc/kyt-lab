from typing import List, Dict, Any
from src.models.transaction import StandardTransaction

class DataNormalizer:
    """
    数据清洗与标准化转换器 (翻译官)。
    负责将底层 DataProvider 获取的各种异构原始数据，
    转换为 KYT 引擎通用的 StandardTransaction 标准数据模型。
    """
    @staticmethod
    def normalize_etherscan(raw_txs: List[Dict[str, Any]]) -> List[StandardTransaction]:
        """
        专门针对 Etherscan 返回的 JSON 数据进行清洗与转换。
        
        参数:
            raw_txs (List[Dict]): Etherscan API 返回的原始字典列表。
            
        返回:
            List[StandardTransaction]: 清洗后的标准交易对象列表。
        """
        standardized_data = []

        for tx in raw_txs:
            try:
                # 1. 识别失败交易与报错信息
                # txlist 接口会返回 isError 和 txreceipt_status，txreceipt_status='0' 或 isError='1' 都代表交易在链上执行失败。is_error接收布尔值
                if tx.get("isError") == "1" or tx.get("txreceipt_status") == "0":
                    is_error = True
                else:
                    is_error = False

                # Etherscan 有时会在 errDescription 给出具体报错，若无则给默认提示。
                err_msg = "Transaction Failed or Reverted" if is_error else ""
                              
                # 2. 判断交易类型并进行金额精度换算
                if tx.get("tokenSymbol"):
                    # ERC-20会有此键值
                    decimals = int(tx.get("tokenDecimal", 18))
                    tokensymbol = str(tx.get("tokenSymbol"))
                else:
                    decimals = 18
                    tokensymbol = "ETH"

                raw_value = float(tx.get("value", 0))
                
                if tokensymbol == "ETH" and raw_value == 0:
                    continue  # 跳过ETH交易中金额为0的交易   

                real_amount = raw_value / (10 ** decimals) 
               
                # 3.根据params中的请求参数，对应Etherscan API，来构造包含状态的标准数据模型
                std_tx = StandardTransaction(
                    tx_hash=str(tx.get("hash", "")),                
                    from_address=str(tx.get("from", "")),
                    to_address=str(tx.get("to", "")),
                    amount=real_amount,
                    timestamp=int(tx.get("timeStamp", 0)),
                    token_symbol=tokensymbol,
                    is_success=not is_error,
                    error_msg=err_msg
                )
                
                standardized_data.append(std_tx)

            except (ValueError, TypeError) as e:
                print(f"[警告]数据清洗异常，跳过交易{tx.get('hash', 'UNKNOWN')}.原因{e}")
                continue

        return standardized_data
