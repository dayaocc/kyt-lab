from collections import defaultdict  # 用来自动分组的数据结构
from .base import BaseDetector
from typing import List, Dict, Any


class PeelchainDetector(BaseDetector):
    """
    动态剥皮链检测插件，两阶段验证模型
    阶段1：单地址大额+小额拆分候选识别
    阶段2：主力资金连续下沉路径验证
    阶段3：全额模式验证
    """
    def __init__(
            self,
            peel_min_ratio: float = 0.01, 
            peel_max_ratio: float = 0.20,
            main_min_ratio: float = 0.5, 
            min_chain_length: int = 3,
            max_step_drop_ratio: float = 0.20
    ):
        # 单笔“小额剥离”占该地址总转出的比例          
        self.peel_min_ratio = peel_min_ratio
        self.peel_max_ratio = peel_max_ratio

        # 主力资金至少占总转出的比例
        self.main_min_ratio = main_min_ratio

        # 至少连续发送多少次Peel交易才能判定为剥皮链
        self.min_chain_length = min_chain_length

        # 主力资金每一层最大允许下降比例
        self.max_step_drop_ratio = max_step_drop_ratio

    def detect(self, trace_tree: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

        alerts = []  # 用来存储检测到的剥皮链风险报告，并作为该检测器结果返回

        # 0.构建图的邻接表
        graph = defaultdict(list)

        for tx in trace_tree:
            sender = tx.get('from') or tx.get('from_address')
            receiver = tx.get('to') or tx.get('to_address')
            amount = float(tx.get('amount', 0))

            if not sender or not receiver or amount <= 0:
                continue

            graph[sender].append({
                "to": receiver, 
                "amount": amount
            })

        # =====阶段1.单地址Peel链候选识别=======
        Peel_candidates = {}    #记录：候选地址 -> 其转出金额列表
        for sender, edges in graph.items():
            total_out = sum(e["amount"] for e in edges)

            if total_out <= 0 or len(edges) < 2:
                continue

            small_peels = []
            main_edge = None

            for edge in edges:
                ratio = edge["amount"] / total_out
                # --小额剥离--                
                if self.peel_min_ratio <= ratio <= self.peel_max_ratio:
                    small_peels.append(edge)

                # --主力资金--
                if ratio >= self.main_min_ratio:
                    # 理论上通常只有一笔主力资金。 如果有多个候选，则选择金额最大的。
                    if (main_edge is None or edge["amount"] > main_edge["amount"]):
                        main_edge = edge
                        
            # 必须同时存在“小额剥离”和“主力资金”才能成为候选
            if small_peels and main_edge:
                Peel_candidates[sender] = {
                    "main_receiver": main_edge["to"],
                    "main_amount": main_edge["amount"],
                    "peel_amounts": [edge['amount'] for edge in small_peels]
                }

        # =====阶段2：路径连续性验证=======
        visited = set()              # 用于记录已经访问过的地址，避免重复追踪

        for start_node in Peel_candidates.keys():
            if start_node in visited:
                continue

            current_node = start_node
            # 记录当前路径和主力资金金额
            chain_path = [current_node]
            # 记录每一层主力资金
            main_amounts = []
            # 记录每一层实际剥离出去的金额
            peel_amounts_by_level = []

            while current_node in Peel_candidates:                
                next_node = Peel_candidates[current_node]["main_receiver"]
                next_main_amount = Peel_candidates[current_node]["main_amount"]
                next_peel_amounts = Peel_candidates[current_node]["peel_amounts"]

                # 如果下一个节点已经在当前路径中出现过，则说明形成了环，停止追踪
                if next_node in chain_path:
                    break

                main_amounts.append(next_main_amount)
                peel_amounts_by_level.append(next_peel_amounts)

                chain_path.append(next_node)

                current_node = next_node

            #=====阶段3：全额模式验证======

            # 3.0 长度校验：如果链条长度未达到最小阈值，则跳过
            if len(main_amounts) < self.min_chain_length:
                continue
            # 3.1 主力资金必须持续下降
            decreasing = all(
                main_amounts[i] > main_amounts[i+1]
                for i in range(len(main_amounts)-1)
                )
            if not decreasing:
                continue

            # 3.2 每一层主力资金下降比例计算
            drop_ratios = []
            for i in range(len(main_amounts)-1):
                current_amount = main_amounts[i]
                next_amount = main_amounts[i+1]

                diff = current_amount - next_amount
                drop_ratio = diff / current_amount
                drop_ratios.append(drop_ratio)

            # 3.3 下降幅度不能太大，不能超过max_step_drop_ratio
            small_step_drop = all(
                0 <= ratio <= self.max_step_drop_ratio
                for ratio in drop_ratios
            )
            if not small_step_drop:
                continue

            # 3.4 如果通过了所有验证，则记录风险报告
            alerts.append({
                "address": start_node,
                "risk_type": "Confirmed Peel Chain",
                "risk_level": "CRITICAL",
                "score": 100,
                "path": chain_path,
                "main_amounts": main_amounts,
                "peel_amounts": peel_amounts_by_level,
                "drop_ratios": drop_ratios,
                "evidence": (
                    f"确认连续剥皮链"
                    f"连续Peel行为{len(main_amounts)}次，"
                    f"资金路径：{' -> '.join(chain_path)}, "
                    f"主力资金变化：{main_amounts}."
                )
            })
            # 确认之后标记visited，避免重复追踪
            for node in chain_path:
                visited.add(node)

        return alerts


        
      

        