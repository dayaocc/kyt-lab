from dataclasses import dataclass
from typing import List, Dict, Set
from database import DatabaseManager
from config import DB_CONFIG
from collections import deque
import pprint


# 追踪引擎核心类，负责分析交易数据、识别风险模式、生成报告等
# 模块1： 任务调度中心
@dataclass
class TraceConfig:
    target_address: str # 监控的地址（可以是钱包地址或合约地址）
    direction: str = 'outflow' # 监控方向，默认为“outflow”，也可以是“inflow”或“both”
    min_amount: float = 0.0 # 最小金额阈值，默认为0，表示监控所有金额的交易
    max_depth: int = 3 # 追踪深度，默认为3层，表示追踪交易链上的3笔交易，防止深挖消耗算力

# 模块2：深度追踪引擎
class TraceEngine:
    def __init__(self, db_manager: DatabaseManager, config: TraceConfig):
        self.db = db_manager
        self.config = config
        
        # 用于记录已经访问过的地址，避免重复追踪
        self.visited_addresses: Set[str] = set()  # visited_addresses是一个集合，里面存放字符串地址
        self.trace_tree: List[Dict] = [] # 用于存储追踪结果的树形结构

        # 预设的风险标签库，混币器或者是cex热钱包的地址是固定的，实际应用中可以更复杂，甚至接入外部威胁情报服务
        self.risk_labels = {
            "0x325428763bc493094E1b7335B8B1da5B7657d604": "Binance热钱包[CEX]",
            "0xtornado_cash_router_address": "Tornado Cash混币服务",
            "0xhacker_group_address": "已知黑客组织地址",
        }
    
    def start_tracing(self):
        """开始追踪指定地址的交易链"""
        print("\n=== 追踪引擎启动 ===")     
        print(f"目标地址： {self.config.target_address}")
        print(f"最大深度： {self.config.max_depth}层")
        print("====================\n")

        # 统一转换为小写，防止大小写不一致导致的匹配问题
        start_address = self.config.target_address.lower()        
        

        # 把起始地址加入"已访问"黑名单集合中
        self.visited_addresses.add(start_address)       

        # 开启广度优先搜索（BFS）追踪交易链
        # 1.初始化排队名单，把起始地址（头号可疑地址）和层级（第0层）以元组的形式加入队列
        queue = deque([(start_address, 0)])
        print(f"开始调查。。。\n")          
        while queue:
            # 1.取出当前要查的地址和它所在的层级
            current_addr, current_depth = queue.popleft() # 从队列头部取出一个地址和对应的层级

            # 2.深度熔断保护：如果已经查到预设的最深层，就跳过他，不再向下深挖，用continue跳出当前循环，开启下一个
            if current_depth >= self.config.max_depth:
                continue
            # 3.调取档案：查询数据库，获取所有与 current_addr 相关的交易
            records = self.db.get_transactions(current_addr)
            print(f"当前在第{current_depth}层，在地址{current_addr}查询到的交易数量为：{len(records)}，正在分析中。。。\n")

            # 4.遍历这些交易记录，对这堆档案 (records)进行分析出来每笔交易的对方地址和金额
            for tx in records:
                # tx的结构通常是(tx_hash, from_addr, to_addr, symbol, amount, timestamp)
                tx_hash = tx['tx_hash']  # tx_hash交易哈希
                to_addr = tx['to_addr']      # to_addr收款人地址
                amount = tx['amount']

                # 5.1.防止无限循环or粉尘攻击，如果有触发，跳出当前for循环
                if (to_addr in self.visited_addresses) or (amount <= self.config.min_amount):
                    continue

                # 5.2.风险标签识别：如果对方地址在预设的风险标签库中，直接标记并记录到线索树形结构中，不再继续追踪这个地址 
                if to_addr in self.risk_labels:
                    self.trace_tree.append(
                        {
                            "tx_hash": tx_hash,
                            "from": current_addr,
                            "to": to_addr,
                            "amount": amount,
                            "current_depth": current_depth,
                            "risk_label": self.risk_labels[to_addr]
                        }
                    )
                    continue


                # 6.确认为有效新线索，加入黑名单并排队
                queue.append((to_addr, current_depth + 1))
                self.visited_addresses.add(to_addr)

                
                # 7.记录到线索树形结构中
                self.trace_tree.append(
                    {
                       "tx_hash": tx_hash,
                       "from": current_addr,
                       "to": to_addr,
                       "amount": amount,
                       "current_depth": current_depth
                    }
                )


        print(f"调查结束，共记录了{len(self.trace_tree)}条关键资金跳转路径。\n")
        return self.trace_tree # 追踪完成后返回整个线索树形结构. return后的代码永远不会执行，所以print写前面
    
    def generate_report(self):
        """根据追踪结果生成分析报告，供后续审计和决策使用"""
        print("\n" + "="*50)
        print("=== 链上资金追踪调查简报 ===")
        print("="*50)

        # 1.调查范围与元数据


# =================测试代码=================

if __name__ == "__main__":

    # 1.创建数据库管理器实例
    db= DatabaseManager(DB_CONFIG)
    
    # 2.定义追踪配置
    test_address = "0x7Ff8bbf9C8AB106db589e7863fb100525F61CCe5"

    warrant = TraceConfig(
        target_address=test_address,                
        max_depth=3
    )
    # 3.创建追踪引擎实例
    engine = TraceEngine(db_manager=db, config=warrant)

    # 4.启动追踪引擎
    results = engine.start_tracing()

    # 5.打印追踪结果    
    print("\n=== 最终输出的线索数据 ===")        
    pprint.pprint(results)