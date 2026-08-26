from typing import List, Dict, Any
from .detectors.base import BaseDetector

class RiskEngine:
    """
    基于多个检测器的风险分析引擎。并按照地址进行风险聚合与画像生成。
    """
    def __init__(self, detectors: List[BaseDetector] = None):
        """依赖注入：允许外部在系统启动时，按需装配检测器列表"""
        self.detectors = detectors or []

    def register_detector(self, detector: BaseDetector):
        """
        注册一个新的风险检测器。
        """
        self.detectors.append(detector)

    def run_analysis(self, trace_tree: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析：
            trace_tree: 标准化的资金追踪路径。
            
        返回:
            Dict: 以地址为 Key 的实体风险画像集合。
        """
        
        raw_alerts = []

        # 1.遍历所有注册的检测器，收集原始风险警报
        for detector in self.detectors:
            raw_alerts.extend(detector.detect(trace_tree))

        # 2.警报聚合
        return self.aggregate_risk_profiles(raw_alerts)

    def aggregate_risk_profiles(self, alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        聚合风险警报，计算总分，生成实体风险画像。
        """
        aggregated = {}
        
        for alert in alerts:            
            address = alert.get("address")

            # 初始化该地址的画像骨架
            if address not in aggregated:
                aggregated[address] = {
                    "total_score": 0,                    
                    "risk_level": "LOW",
                    "tags": set(),      # 使用集合自动去重风险标签
                    "alerts": []        # 记录所有触发的警报详情
                }

            # 累加风险分数
            aggregated[address]["total_score"] += alert.get("score", 0)
            aggregated[address]["tags"].add(alert.get("label", "UNKNOWN"))
            aggregated[address]["alerts"].append({
                "severity": alert.get("severity", "UNKNOWN"),
                "evidence": alert.get("evidence", {}),
            })

        # 3.根据总分计算最终风险等级
        for addr, profile in aggregated.items():
            total_score = profile["total_score"]
            if total_score >= 100:
                profile["risk_level"] = "CRITICAL"
            elif total_score >= 60:
                profile["risk_level"] = "HIGH"
            elif total_score >= 30:
                profile["risk_level"] = "MEDIUM"
            else:
                profile["risk_level"] = "LOW"

            # 将标签集合转换为列表,保证后续导出或 API 输出时能够正常进行 JSON 序列化
            profile["tags"] = list(profile["tags"])

        return aggregated