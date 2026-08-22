from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseDetector(ABC):
    """
    风险检测器基类 (Base Detector)。
    所有具体的风险检测器都应继承自此类，并实现 detect 方法。
    """
    @abstractmethod
    def detect(self, trace_tree: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        抽象方法：执行洗钱/风险特征检测逻辑。
        
        参数:
            trace_tree 由TraceEngine 产出的资金追踪线索树。
            
        返回:
            List[Dict]: 检测结果列表(Risk Alerts)，每条结果为一个字典，包含嫌疑实体、风险类型、危险等级及证据等信息。
        """
        pass