import networkx as nx
# import matplotlib.pyplot as plt
from pyvis.network import Network
import os

class GraphBuilder:
    def __init__(self):
        # 创建一个空的有向图对象，用于存储交易链路
        self.graph = nx.DiGraph()

    def build_from_trace(self, trace_tree):
        """
        将trace_engine生成的线索树形结构转换为网络图谱
        """
        for t in trace_tree:
            sender = t['from']
            receiver = t['to']
            amount = t.get('amount')
            # 适用networkx的DiGraph对象的add_edge方法添加带有金额属性的有向边
            self.graph.add_edge(
                sender, 
                receiver, 
                amount=t.get('amount'),
                tx_hash=t.get('tx_hash'),
                depth=t.get('current_depth'),
                detector=t.get('detector'),
                risk=t.get('risk_label')
                )
        return self.graph
    
    def generate_interactive_html(self, output_filepath):
        """将内存中的图谱渲染为可视化窗口"""


#         plt.figure(figsize=(12, 8))  # 设置画布大小

#         # 1.布局算法：决定节点在画布上的位置 (spring_layout 会让关联的节点靠在一起)
#         pos = nx.spring_layout(self.graph, seed=42)
#         # 2. 画出节点和连线  
#         nx.draw(self.graph,
#                 pos, 
#                 with_labels=True,           # 显示节点名称
#                 node_color='lightblue',     # 节点颜色
#                 node_size=2500,             # 节点大小
#                 font_size=9,                # 字体大小
#                 font_weight='bold',
#                 arrows=True,                # 显示资金流向箭头
#                 edge_color='gray'
#                 )
#         # 3. 提取边上的 amount 属性，并画在连线上      
#         edge_labels = nx.get_edge_attributes(self.graph, 'amount')  
#         nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels, font_color='red', font_size=8)

#         plt.title("链上资金流向图谱", fontsize=16)
#         plt.show()      # 弹出可视化窗口



        # 使用pyvis进行可视化
        net = Network(
            height='800px',
            width='100%',
            directed=True,
            bgcolor="#ffffff",
            font_color="black"
            )
        # 将networkx的图对象转换为pyvis的网络对象
        net.from_nx(self.graph)
        for edge in net.edges:
            amount = edge.get('amount', 0)
            if amount is not None:
                edge["label"] = str(amount)
                edge["title"] = f" TransferAmount: {amount}"
        
        for node in net.nodes:
            node_id_lower = str(node['id']).lower()
            node["title"] = f"Address: {node['id']}"
            node["size"] = 25 
            node["color"] = "lightblue"  # 可以根据需要调整节点颜色
            if "hacker" in node_id_lower:
                node["color"] = "red"  # 如果节点是黑客地址，标记为红色
                node["size"] = 30  # 黑客节点更大
            elif "冷钱包" in node_id_lower:
                node["color"] = "#800080"       #紫色
            elif "Vault" in node_id_lower:
                node["color"] = "green"  # 如果节点是资金池地址，标记为绿色
                
        os.makedirs(os.path.dirname(os.path.abspath(output_filepath)), exist_ok=True)

        # net.show_buttons(filter_=['physics'])  # 显示物理引擎按钮，方便调整布局
        # net.write_html("transaction_graph.html")  # 将图谱保存为HTML文件并在浏览器中打开
        
        net.save_graph(output_filepath)  # 将图谱保存为HTML文件
        print(f"资金关系图图谱已保存至: {output_filepath}")