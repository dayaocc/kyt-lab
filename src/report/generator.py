import os
from datetime import datetime
from typing import List, Dict, Any
from jinja2 import Template

class ReportGenerator:
    """
    调查报告自动生成模块。
    将 TraceEngine 和 RiskEngine 的输出数据聚合，通过 Jinja2 模板渲染成标准的 Markdown 报告。
    """
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        # 先把预设的md模板用字符串的形式装进self.template_str中
        self.template_str = """
KYT 链上资金追踪与合规调查报告
**生成时间：** {{ generated_time }}
**调查目标地址：** `{{ target_address }}`
--------------------
## 1.执行摘要
本次调查针对目标地址 `{{ target_address }}` 展开了链上资金流向分析，追踪深度为 **{{ max_depth }}** 层。
系统共抓取并分析了 **{{ total_txs }}** 条有效转账记录，涉及 **{{ unique_addresses }} **个独立链上地址。

经过风险引擎（Risk Engine）的模型测算与库碰撞，共发现 **{{ risk_entities_count }}** 个命中风险规则或已知风险标签的实体。

## 2. 高危风险实体剖析
{% if risk_profiles %}
{% for address, profile in risk_profiles.items() %}
### 🔴 实体地址: `{{ address }}`
* **综合风险评级:** ** {{ profile.risk_level }}**,  (风险总分: {{ profile.total_score }})
* **命中的风险标签:**  {{ profile.tags | join(', ') }}
* **固化证据链:**
{% for alert in profile.alerts %}
  * [{{ alert.severity }}] {{ alert.evidence }}
{% endfor %}
{% endfor %}
{% else %}
> 暂未在追踪链路中检测到明确的高危实体或典型的洗钱模式。
{% endif %}

## 3. 资金流转统计 (Fund Flow Overview)
* **追踪起始点:**  `{{ target_address }}`
* **总流转笔数:**  {{ total_txs }} 笔
* **涉及的代币资产:**  {{ tokens | join(', ') }}


## 4. 调查结论与建议 (Conclusion & Recommendations)
{% if risk_entities_count > 0 %}
**结论:** 
目标地址及其下游资金路径命中了已知高风险实体，存在明显的风险交互行为。具体风险类型及证据见上述风险实体画像。
**建议:**
1. 建议将上述检测到的高危地址列入内部业务监控黑名单。
2. 结合可视化交互图谱（`transaction_graph.html`），进一步人工核实资金的最终沉淀节点（如审查是否流入了可冻结资产的中心化交易所 CEX）。
{% else %}
**结论:** 
目标地址下游流转暂未表现出标准的机器可识别风险。
**建议:** 
继续保持被动监控，或适当扩大追踪层级以排查深层隐藏风险。
{% endif %}
        
"""

    def generate_markdown(
        self, 
        target_address: str, 
        trace_tree: List[Dict[str, Any]], 
        risk_profiles: Dict[str, Any],        
        filename: str = "investigation_report.md" 
    ) -> str:
        
        """进行数据统计，并渲染模板 """

        unique_addresses = set()
        tokens = set()
        max_depth = 0

        for tx in trace_tree:
            unique_addresses.add(tx.get("from"))
            unique_addresses.add(tx.get("to"))
            tokens.add(tx.get("symbol", "UNKNOWN"))

            depth = tx.get("current_depth", 0) + 1

            if depth > max_depth:
                max_depth = depth

        # 删除无效空数据
        unique_addresses.discard(None)
        unique_addresses.discard("")

        tokens.discard("")
        tokens.discard(None)

        # 准备给jinja解析用的数据
        context = {
            "generated_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "target_address": target_address,
            "max_depth": max_depth,
            "total_txs": len(trace_tree),
            "unique_addresses": len(unique_addresses),
            "risk_profiles": risk_profiles,
            "risk_entities_count": len(risk_profiles),
            "tokens": list(tokens),            
        }

        # 把template_str字符串转换为jinja对象
        template = Template(self.template_str)

        # 把context数据填入template对象中，**是字典解包.
        rendered_md = template.render(**context)

        # 写入文件
        output_filepath = os.path.join(self.output_dir, filename)
        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(rendered_md)

        print(f"[报告生成] 调查报告已经生成：{output_filepath}")
        return output_filepath