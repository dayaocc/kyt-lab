from collections import defaultdict

class RiskEngine:
    def __init__(self):
        # 风险评级标准矩阵
        self.level_matrix = {
            "CRITICAL": 90,     # 致命风险：直接冻结/阻断
            "HIGH": 70,         # 高危：限制提币，人工审核
            "MEDIUM": 40,       # 中风险：持续监控
            "LOW": 0,           # 低风险：正常放行
        }

        # 多重违规的惩罚系数 (例如：触发一个新规则，在最高分基础上加 10 分)
        self.penalty_weight = 10
    
    def _determine_level(self, score):
        """
        根据最终风险评分确定风险等级。
        """
        if score >= self.level_matrix['CRITICAL']:
            return "CRITICAL"
        elif score >= self.level_matrix['HIGH']:
            return "HIGH(高危)"
        elif score >= self.level_matrix['MEDIUM']:
            return "MEDIUM(中风险)"
        else:
            return "LOW(低风险)"
    
    def generate_comprehensive_profiles(self, raw_reports):
        """
        接收所有孤立的警报碎片，融合成每个地址的最终档案
        """
        # 1. 实体分组：把同一个嫌疑人的所有报告归拢到一起
        grouped_reports = defaultdict(list)
        for report in raw_reports:
            grouped_reports[report['sender']].append(report)
        
        final_profiles = {}

        # 2. 档案融合与综合打分
        for address, reports in grouped_reports.items():

            # 提取该地址触发的所有分数和标签
            all_scores = [r['score'] for r in reports]
            all_labels = [r['label'] for r in reports]

            # 综合评分算法：最高分 + (额外违规次数 * 惩罚分)，最高封顶 100 分
            base_scores = max(all_scores)
            extra_violations = len(all_scores) - 1  # 除了最高分之外的额外违规次数
            final_score = min(100, base_scores + extra_violations * self.penalty_weight)

            # 去重并合并标签
            unique_labels = list(set(all_labels))  # list使集合转换为列表

            # 提取具体的犯罪证据链 (如果有的话)
            evidence_details = []
            for r in reports:
                if "path_amounts" in r:
                    evidence_details.append(f"资金流向{r['path_amounts']}")
                if "details" in r:
                    evidence_details.append(f"制裁名单详情{r['details'].get('entity','Unknown')}")
            
        # 3.生成最终档案
            final_profiles[address] = {
                "address": address,
                "final_score": final_score,
                "risk_level": self._determine_level(final_score),
                "labels": unique_labels,
                "evidence": evidence_details,
                "violations_count": len(reports)
            }
        
        return final_profiles