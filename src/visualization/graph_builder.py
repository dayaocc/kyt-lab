from pyvis.network import Network
import os
from typing import List, Dict, Any, Optional
import networkx as nx

class GraphBuilder:
    """
    资金流可视化组件
    职责：
    1. 接收 TraceEngine 输出的 trace_tree
    2. 接收 RiskEngine 输出的 risk_profiles
    3. 构建有向资金流图
    4. 使用 PyVis 输出交互式 HTML 图谱
    """
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(
            self.output_dir,
            exist_ok=True
        )       

        self.graph = nx.MultiDiGraph()      # MultiDiGraph()是networkx库中的有向多重图类

    @staticmethod
    def _short_address(address: str) -> str:
        """  缩短地址用于图谱显示    """

        if len(address) <= 16:
            return address
        return f"{address[:8]}...{address[-6:]}"
    

    def build_from_trace(
            self, 
            trace_tree: List[Dict[str, Any]],
            risk_profiles: Optional[Dict[str, Any]] = None,
            seed_address: Optional[str] = None      # 标记追踪起点
    ):
        """        
        将 TraceEngine 生成的 trace_tree
        转换为 NetworkX 有向资金图谱        
        """
        # 构图前先清空旧图
        self.graph.clear()

        risk_profiles = risk_profiles or {}

        # 地址全部转小写
        if seed_address:
            seed_address = seed_address.lower()

        normalized_risk_profiles = {
            str(address).lower(): profile for address, profile in risk_profiles.items()
        }

        for tx in trace_tree:
            sender = (tx.get("from") or "").lower()
            receiver = (tx.get("to") or "").lower()
            if not sender or not receiver:
                continue

            amount = tx.get("amount", 0) 
            symbol = tx.get("symbol", "")
            tx_hash = tx.get("tx_hash", "")
            depth = tx.get("current_depth", 0)

            # 1.添加发送方节点
            self._add_node(
                address=sender,
                seed_address=seed_address,
                risk_profiles=normalized_risk_profiles
            )

            # 2.添加接收方节点
            self._add_node(
                address=receiver,
                seed_address=seed_address,
                risk_profiles=normalized_risk_profiles
            )

            # 3.添加资金流向边
            self.graph.add_edge(
                sender, 
                receiver, 
                amount=amount,
                symbol=symbol,
                tx_hash=tx_hash,
                depth=depth,                
                title=(
                    f"Amount:{amount:,.4f} {symbol}<br>"
                    f"TxHash: {tx_hash}<br>"
                    f"Depth: {depth}"
                )             
            )
        return self.graph

    def _add_node(
            self,
            address: str,
            seed_address: Optional[str],
            risk_profiles: Dict[str, Any]
    ):
        """
        添加节点，并根据 seed / risk_profiles
        设置节点属性
        """
        # 节点已经存在就不重复添加
        if address in self.graph:
            return
        profile = risk_profiles.get(address, {})

        # 默认节点属性
        node_type = "normal"
        color = "lightblue"
        size = 25

        # 定义起点地址属性
        if address == seed_address:
            node_type = "seed"
            color = "orange"
            size = 35

        # riskengine检测出的风险地址
        if profile:
            node_type = "risk"
            risk_level = (
                profile.get("risk_level")
                or profile.get("severity")
                or "HIGH"
            )
            if risk_level == "CRITICAL":
                color = "red"
                size = 35
            elif risk_level == "HIGH":
                color = "#ff6666"       # 浅红色    
                size = 30
            elif risk_level == "MEDIUM":
                color = "yellow"
                size = 28
        
        title = f"Address: {address}"

        if profile:
            title += "<br><br>Risk Profile:"
            title += f"<br>{profile}"

        self.graph.add_node(
            address,
            label=self._short_address(address),
            title=title,        # 其中包含了risk_profile的
            node_type=node_type,
            color=color,
            size=size
        )

    
    def generate_interactive_html(self, output_filepath):
        """将内存中的NetworkX图谱
        渲染为PyVis HTML 可视化窗口"""
     
        # 生成pyvis图，进行可视化
        net = Network(
            height='800px',
            width='100%',
            directed=True,
            bgcolor="#ffffff",
            font_color="black"
            )
        
        # 将networkx的图对象转换为pyvis的网络对象
        net.from_nx(self.graph)

        # ----处理边----
        for edge in net.edges:

            amount = edge.get("amount", 0)
            symbol = edge.get("symbol", "")
            tx_hash = edge.get("tx_hash", "")
            depth = edge.get("depth", "")

            edge["label"] = f"{amount:,.4f} {symbol}"

            edge["title"] = (
                f"Amount: {amount:,.4f} {symbol}\n"
                f"TxHash: {tx_hash}\n"
                f"Depth: {depth}"
            )

            edge["arrows"] = "to"

        # -----处理节点----
        for node in net.nodes:

            node.setdefault("size", 25)
            node.setdefault("color", "lightblue")

        # 自动物理布局
        net.barnes_hut()

        os.makedirs(
            os.path.dirname(os.path.abspath(output_filepath)),exist_ok=True
        )    

        # 生成包含 HTML + JavaScript 的网页文件 
        net.save_graph(output_filepath)

        print(f"资金关系图谱已经保存至：{output_filepath}")

        return output_filepath



            