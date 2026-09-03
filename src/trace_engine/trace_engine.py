from dataclasses import dataclass
from typing import List, Dict, Set
from collections import deque
import pprint

from src.data_collection.chain_listener import ChainListener



# 追踪引擎核心，负责从起始地址进行多跳资金追踪，生成 trace_tree
# 模块1： 任务调度中心
@dataclass
class TraceConfig:
    target_address: str             # 监控的地址（可以是钱包地址或合约地址）
    direction: str = 'outflow'      # 监控方向，默认为“outflow”，也可以是“inflow”或“both”
    min_amount: float = 0.0         # 最小金额阈值，默认为0，表示监控所有金额的交易
    max_depth: int = 3              # 追踪深度，默认为3层，表示追踪交易链上的3笔交易，防止深挖消耗算力
    start_block: int = 0
    end_block: int = 99999999

# 模块2：深度追踪引擎
class TraceEngine:
    def __init__(self, listener: ChainListener, config: TraceConfig):
        self.listener = listener
        self.config = config
        
        # 用于记录已经访问过的地址，避免重复追踪
        self.visited_addresses: Set[str] = set()    # visited_addresses是一个集合，里面存放字符串地址
        self.trace_tree: List[Dict] = []            # 用于存储追踪结果的树形结构
    
    def start_tracing(self):
        """开始追踪指定地址的交易链"""
        print("\n=== 追踪引擎启动 ===")     
        print(f"目标地址： {self.config.target_address}")
        print(f"最大深度： {self.config.max_depth}层")
        print("====================\n")
        
        start_address = self.config.target_address.lower()      
        
        # 把起始地址加入"已访问"黑名单集合中
        self.visited_addresses.add(start_address)       

        # 开启广度优先搜索（BFS）追踪交易链
        # 1.初始化排队名单，把起始地址（头号可疑地址）和层级（第0层）以元组的形式加入队列
        queue = deque([
            (start_address, 0, 0)
        ])
                 
        while queue:

            # 1.取出当前要查的地址和它所在的层级
            current_addr, current_depth, incoming_timestamp = queue.popleft() # 从队列头部取出一个地址和对应的层级

            # 2.深度熔断保护：如果已经查到预设的最深层，就跳过他，不再向下深挖，用continue跳出当前循环，开启下一个
            if current_depth >= self.config.max_depth:
                continue

            # 3.调取档案：直接通过 ChainListener 获取真实链上交易
            records = self.listener.get_transactions(
                address=current_addr,
                start_block=self.config.start_block,
                end_block=self.config.end_block 
            )
            print(f"当前在第{current_depth}层，在地址{current_addr}查询到的交易数量为：{len(records)}，正在分析中。。。\n")

            # 4.遍历这些交易记录，对这堆档案 (records)进行分析出来每笔交易的对方地址和金额
            for tx in records:
                # 只处理成功交易
                if not tx.is_success:
                    continue

                # 只处理时间戳晚于当前地址的交易，避免回溯
                if tx.timestamp < incoming_timestamp:
                    continue    

                from_addr = tx.from_address.lower()
                to_addr = tx.to_address.lower()
                amount = tx.amount   

                # 5.1 限定资金方向，先做outflow
                if self.config.direction == "outflow":
                    if from_addr != current_addr:
                        continue
                    next_addr = to_addr
                else:
                    continue

                
                # 5.2 金额过滤
                if amount <= self.config.min_amount:
                    continue

                # 5.3 记录资金路径                
                self.trace_tree.append(
                    {
                        "tx_hash": tx.tx_hash,
                        "from": from_addr,
                        "to": to_addr,
                        "amount": amount,
                        "symbol": tx.token_symbol,
                        "current_depth": current_depth,
                        "timestamp": tx.timestamp                            
                    }
                )
                 
                if next_addr in self.visited_addresses:
                    continue

                self.visited_addresses.add(next_addr)                   

                # 6.确认为有效新线索，加入黑名单并排队
                queue.append((next_addr, current_depth + 1, tx.timestamp))
                                                 
                         
        print(f"调查结束，共记录了{len(self.trace_tree)}条资金跳转路径。\n")

        return self.trace_tree 

    
   


