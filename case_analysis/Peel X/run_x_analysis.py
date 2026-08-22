import sys
import os
import pprint
import json


# 1. 动态连接：将 src 目录加入系统路径，以便导入纯净的核心引擎
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, '../../src'))

print(src_dir)

sys.path.append(src_dir)

# 从 src 引擎库导入工具
from visualization.graph_builder import GraphBuilder
from trace_engine.trace_engine import TraceEngine, TraceConfig
from risk_analysis.risk_engine import RiskEngine
from risk_analysis.detectors.peel_chain import PeelchainDetector

from infrastructure.database import DatabaseManager
from infrastructure.config import DB_CONFIG

class MockDatabase:
    def __init__(self, json_filepath):
        self.json_filepath = json_filepath
        # 如果json不存在，模拟chain_listener自动生成一份原始抓取数据
        if not os.path.exists(json_filepath):
            self._generate_mock_json()
    
        with open(self.json_filepath, 'r', encoding='utf-8') as f:
            self.all_transactions = json.load(f)

    def _generate_mock_json(self):
        """模拟将抓取到的数据保存至json文件"""
        mock_data = [
            {"tx_hash": "0x111", "from_addr": "0x_Hacker", "to_addr": "0x中转钱包a", "amount": 450000},
            {"tx_hash": "0x222", "from_addr": "0x_Hacker", "to_addr": "0x场外交易商1", "amount": 50000},
            {"tx_hash": "0x333", "from_addr": "0x中转钱包a", "to_addr": "0x中转钱包b", "amount": 410000},
            {"tx_hash": "0x444", "from_addr": "0x中转钱包a", "to_addr": "0x场外交易商2", "amount": 40000},
            {"tx_hash": "0x555", "from_addr": "0x中转钱包b", "to_addr": "0x沉淀冷钱包", "amount": 375000},
            {"tx_hash": "0x666", "from_addr": "0x中转钱包b", "to_addr": "0x场外交易商3", "amount": 35000}
        ]
        with open(self.json_filepath, 'w', encoding='utf-8') as f:
            json.dump(mock_data, f, indent=4, ensure_ascii=False)

    def get_transactions(self, address):
        return [tx for tx in self.all_transactions if tx['from_addr'] == address]


# 2.注入专属数据：UPCX 案件的资金流
# raw_transactions = [
#     {'from': '0xUPCX_Vault', 'to': '0xUPCX_Hacker', 'amount': 500000},
#     {'from': '0xRandomUser', 'to': '0xExchange', 'amount': 100}, # 噪音数据
#     {'from': '0xUPCX_Hacker', 'to': '0x中转钱包A', 'amount': 450000},
#     {'from': '0xUPCX_Hacker', 'to': '0x场外交易商1', 'amount': 50000},
#     {'from': '0x中转钱包A', 'to': '0x中转钱包B', 'amount': 410000},
#     {'from': '0x中转钱包A', 'to': '0x场外交易商2', 'amount': 40000},
#     {'from': '0x中转钱包B', 'to': '0x沉淀冷钱包', 'amount': 375000},
#     {'from': '0x中转钱包B', 'to': '0x场外交易商3', 'amount': 35000}
# ]
if __name__ == "__main__":
    print("=== X 案件分析 ===")
    json_path = os.path.join(current_dir, 'x_raw_data.json')
    print(f"本地数据文件路径位于:{json_path}")
    mock_db = MockDatabase(json_path)
    # # 1.数据库连接与资金追踪
    # db = DatabaseManager(DB_CONFIG)

    # 配置案件并追踪
    upcx_config = TraceConfig(
        target_address="0x_Hacker", 
        max_depth=3
    )

    print("正在执行链上资金追踪（BFS）")
    # 2. 启动链上追踪引擎    
    tracer = TraceEngine(db_manager=mock_db, config=upcx_config)
    x_trace_tree = tracer.start_tracing()

    # 风险判定
    # 3. 调用探测器提取特征识别和风险判定    
    detector = PeelchainDetector()
    raw_transactions = detector.detect(x_trace_tree)

    risk_engine = RiskEngine()
    risk_profiles = risk_engine.generate_comprehensive_profiles(raw_transactions)

    print("===最终嫌疑人高危档案====")
    pprint.pprint(risk_profiles)   

    # 4. 生成可视化图谱
    print("正在生成案件证据图谱：")
    builder = GraphBuilder()
    builder.build_from_trace(x_trace_tree)
    
    output_html_path = os.path.join(current_dir, 'x_graph.html')
    builder.generate_interactive_html(output_html_path)
    print(f"分析完毕！图谱已保存至: {output_html_path}")