import json
import os
from typing import List, Dict, Any
from .base import BaseDetector

class SanctionDetector(BaseDetector):
    """
    制裁名单检测器 (Sanction List Detector)。
    用于检测trace_tree中的地址是否涉及制裁名单上的实体。
    """
    def __init__(self, list_path: str = None):
        """
        初始化制裁名单检测器。
        
        参数:
            list_path: 制裁名单文件的路径，文件应为 JSON 格式，包含制裁实体信息。
        """

        if list_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            list_path = os.path.abspath(os.path.join(current_dir, '../../data/sanction_list.json'))

        self.sanction_data = self.load_sanction_list(list_path)

    def load_sanction_list(self, path: str) -> Dict[str, Any]:
        """
        加载json制裁名单。并在内存中将所有地址转换为小写以防匹配失败     
        """

        try: 
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {k.lower(): v for k, v in data.items()}
        except FileNotFoundError:
            print(f"[SanctionDetector]警告：制裁名单文件未找到: {path}")
            return {}
        except json.JSONDecodeError:
            print(f"[SanctionDetector]错误：标签库 JSON 格式损坏: {path}")
            return {}

    def detect(self, trace_tree: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        检测trace_tree中的地址是否涉及制裁名单上的实体。
        
        参数:
            trace_tree: 由TraceEngine产出的资金追踪线索树。
            
        返回:
            List[Dict]: 检测结果列表(Risk Alerts)，每条结果为一个字典，包含嫌疑实体、风险类型、危险等级及证据等信息。
        """
        alerts = []
        flagged_addresses = set()  # 用于记录已标记的地址，避免重复报警

        for tx in trace_tree:
            # 提取交易的收发地址并转为小写
            sender = (tx.get('from') or tx.get('from_address', '')).lower()
            receiver = (tx.get('to') or tx.get('to_address', '')).lower()

            for address in (sender, receiver):
                if not address or address in flagged_addresses:
                    continue  # 跳过空地址或已标记的地址

                if address in self.sanction_data:
                    entity_info = self.sanction_data[address]
                    risk_level = entity_info.get('risk_level', 'HIGH')  
                    
                    if risk_level in ["CRITICAL", "HIGH"]:

                        score = 100 if risk_level == "CRITICAL" else 75

                        alerts.append({
                            "address": address,
                            "risk_type": entity_info.get('type', 'High Risk Entity'),
                            "risk_level": risk_level,
                            "score": score,
                            "evidence": f"直接命中高危实体标签库，实体名称：{entity_info.get('name', 'Unknown')}"
                        })
                        
                        flagged_addresses.add(address)  # 标记该地址已报警，避免重复报警

        return alerts