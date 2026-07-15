
#  KYT-Lab: On-chain Compliance & Trace Analysis Engine

KYT-Lab 是一个模块化、自动化的链上风险分析与资金追踪系统。专为 Web3 反洗钱 (AML) 与安全事件追踪设计。

##  核心能力 (Core Features)
* **深度追踪 (TraceEngine)**: 基于 BFS 算法的资金下钻溯源，内置粉尘攻击过滤与深度熔断机制。
* **特征识别 (RiskAnalysis)**: 自动化识别复杂的洗钱手法（如 Peel Chain 动态剥皮链、Automated Fan-out 自动化打散）。
* **综合判定 (RiskEngine)**: 聚合多维警报，生成 0-100 分制的实体高危档案。
* **可视化取证 (GraphBuilder)**: 将底层交易流转化为直观的交互式资金网络图谱。

##  经典案例：剥皮链洗钱案例 X
在 `case_studies/Peel X/` 目录下，展示了系统如何处理一起真实的链上安全事件：
1. `run_x_analysis.py`: 全链路自动化追踪脚本。
2. `x_raw_data.json`: 模拟抓取的底层链上 Raw Data。
3. `x_graph.html`: 引擎生成的交互式证据图谱。
4. `X_Investigation_Report.md`: 最终输出符合链上调查流程的分析报告。

##  快速启动 (Quick Start)
```bash
# 运行 X 案件全链路分析流水线
cd case_studies/Peel X
python run_x_analysis.py
