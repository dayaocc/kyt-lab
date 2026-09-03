import requests
from typing import List, Dict, Any
from .base import DataProvider
import time
from datetime import datetime, timezone

class EtherscanProvider(DataProvider):
    """
    Etherscan 数据源实现类。
    负责通过 Etherscan REST API 获取真实的以太坊链上交易数据。
    """

    def __init__(
            self, 
            api_key: str, 
            base_url: str = "https://api.etherscan.io/v2/api",
            max_retries: int = 3,       # 网络请求失败时，最多尝试3次
            timeout: int = 10           # 每次请求等待时间
    ):
        """
        初始化 Etherscan Provider。
        
        参数:
            api_key (str):  Etherscan API 密钥
            base_url (str): API 端点。如果是 BSC 链可以替换为 bscscan 的 url。
        """

        self.api_key = api_key      
        self.base_url = base_url  
        self.max_retries = max_retries
        self.timeout = timeout

    def get_block_by_date(
            self,
            date_str: str, 
            closest: str = "before"
        ) -> int:
        dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

        timestamp = int(dt.timestamp())

        params = {
            "chainid": 1,
            "module": "block",
            "action": "getblocknobytime",
            "timestamp": timestamp,
            "closest": closest,
            "apikey": self.api_key
        }
        print(
            f"[Etherscan API]日期转区块：{date_str} → timestamp={timestamp}"
        )

        response = requests.get(
            self.base_url,
            params=params, 
            timeout=self.timeout
        )

        data = response.json()

        return int(data["result"])

    def fetch_transactions(self, address: str, **kwargs) -> List[Dict[str, Any]]:
        """
        从 Etherscan 获取指定地址的原始交易记录。
        
        支持的 kwargs 扩展参数:
            tx_type (str): 'tokentx' (获取 ERC-20 代币转账, 默认) 
                           或 'txlist' (获取 ETH 主币转账)
            start_block (int): 起始区块高度 (默认 0)
            end_block (int): 结束区块高度 (默认 99999999)
        """
        # 从 kwargs 中提取参数，如果没传则使用默认值.
        tx_type = kwargs.get("tx_type", "tokentx")
        start_block = kwargs.get("start_block", 0)
        end_block = kwargs.get("end_block", 999999999)

        # 设置发送给 Etherscan 的请求参数
        params = {
            "chainid":1,
            "module": "account",
            "action": tx_type,
            "address": address,
            "startblock": start_block,
            "endblock": end_block,
            "page": 1,
            "offset": 10000,    # 每次最大获取 10000 条记录
            "sort": "asc",      # 按时间正序排列（从旧到新）
            "apikey": self.api_key
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                print(
                    f"[Etherscan API] 正在请求{address}"
                    f"(第{attempt}/{self.max_retries}次)"
                )
                # 发起 HTTP GET 请求
                response = requests.get(self.base_url, params=params, timeout=self.timeout)

                #检查 HTTP 网络状态码 (替代了直连 RPC 时的 simple_check)
                # 200请求成功。429请求太频繁，403禁止访问，500服务器错误
                if response.status_code != 200:
                    print(f"[错误]HTTP请求失败，状态码：{response.status_code}")

                    # 最后一次还失败，则返回[]。不再重试
                    if attempt == self.max_retries:
                        return []

                    # 指数退避
                    time.sleep(2 ** (attempt - 1))
                    continue

                data = response.json()      # 把json转成python字典

                print("请求URL：", response.url)
                # print("Etherscan原始返回", data)

                # 检查 Etherscan 业务状态码,1表示业务成功
                if data.get("status") == "1":
                    raw_txs = data.get("result", [])
                    print(f"[Etherscan API]成功获取地址 {address} 的{len(raw_txs)}条{tx_type}记录")
                    return raw_txs
                else:
                    # Etherscan 如果没查到数据，通常返回 status '0' 和 message 'No transactions found'
                    print(f"[Etherscan API]未获取到数据或发生异常：{data.get('message')}")
                    return []
            except requests.exceptions.RequestException as e:            
                print(f"[网络异常] 第{attempt}/{self.max_retries}次请求 Etherscan API 时失败: {e}")

                if attempt == self.max_retries:
                    print(
                        f"[Etherscan API] 已重试 {self.max_retries} 次，仍然失败。"
                    )
                    return []

                # 指数退避：1s → 2s → 4s
                wait_time = 2 ** (attempt - 1)
                print(
                    f"[Etherscan API] {wait_time} 秒后进行第 {attempt + 1} 次重试..."
                )
                time.sleep(wait_time)
        return []
