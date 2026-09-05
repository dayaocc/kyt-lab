# KYT-Lab

**On-chain Risk & Transaction Tracing Prototype**

KYT-Lab 是一个面向 Web3 合规分析与链上调查场景的个人项目。项目从 Ethereum 原始交易数据出发，完成 **数据采集 → 标准化 → 多跳资金追踪 → 风险规则检测 → 风险聚合 → 图谱与调查报告输出** 的完整闭环。

> 项目定位：用于学习和验证 KYT / 链上风险分析方法，不是生产级合规系统。

## Core Features

- **Ethereum 数据采集**：通过 Etherscan V2 API 同时获取 ETH 主币交易（`txlist`）与 ERC-20 转账（`tokentx`）。
- **统一交易模型**：将原始 API 数据标准化为 `StandardTransaction`，处理 decimals、失败交易、时间戳等字段。
- **多跳资金追踪**：`TraceEngine` 基于 BFS 进行下游资金追踪，支持方向、最小金额、最大深度与区块窗口控制。
- **时间因果过滤**：为每一跳保存资金到达时间，过滤早于上游资金到达时间的历史交易，减少繁忙 DEX / Pool 地址带来的无关噪音。
- **规则型风险检测**：通过插件式 Detector 识别已知风险实体及 Peel Chain 特征。
- **风险聚合**：`RiskEngine` 聚合风险类型、等级、分数与证据，形成地址级风险画像。
- **分析交付**：使用 NetworkX + PyVis 输出交互式资金图谱，使用 Jinja2 自动生成 Markdown 调查报告。

## Analysis Pipeline

```text
Etherscan V2 API
      ↓
EtherscanProvider
      ↓
ChainListener
      ↓
DataNormalizer
      ↓
StandardTransaction
      ↓
TraceEngine (BFS + time-causality filter)
      ↓
Detectors
  ├─ SanctionDetector
  └─ PeelChainDetector
      ↓
RiskEngine
      ↓
JSON / PyVis HTML / Markdown Report
```

## Case Study: Harmony Horizon Bridge

项目使用 2022 年 Harmony Horizon Bridge 事件进行真实链上数据复盘，以公开的攻击者地址作为调查起点，在限定时间窗口内追踪其后续资金流向。

本次运行结果：

| Metric | Result |
| --- | ---: |
| Trace depth | 3 hops |
| Transactions after filtering | 8,596 |
| Unique addresses | 1,645 |
| High-risk entities identified | 2 |
| Tornado Cash related sender addresses | 14 |
| ETH transfers to Tornado Cash Router | 857 |
| Total ETH to Tornado Cash Router | 85,700 ETH |

时间因果过滤加入前，系统会把部分繁忙地址在“可疑资金到达之前”的历史交易错误纳入下游路径；修复后交易数从 **13,484 降至 8,596**，地址数从 **2,449 降至 1,645**，同时保留了 Harmony → Tornado Cash 的核心资金路径。

系统识别出的 **14 个关联地址、约 85,700 ETH 流入 Tornado Cash Router** 与公开案件复盘的核心统计一致。

运行：

```bash
python -m case_analysis.harmony_horizon.run_harmony_analysis
```

主要输出：

```text
case_analysis/harmony_horizon/results/
├── analysis_result.json
├── transaction_graph.html
└── harmony_investigation_report.md
```

## Other Case

`case_analysis/UPCX/`：用于验证通用追踪、风险检测和报告生成流程的另一组链上案例。

## Tech Stack

`Python` · `Requests` · `Etherscan API` · `NetworkX` · `PyVis` · `Jinja2` · `Git`

## Current Limitations

- 当前主要基于 `txlist + tokentx`，尚未完整解析 internal transactions 与复杂智能合约调用语义。
- 时间因果目前基于秒级 timestamp；同一区块内的严格顺序未来可进一步使用 `blockNumber / transactionIndex / logIndex` 判断。
- Mixer 会切断确定性的资金关联，因此当前系统在 Tornado Cash 等混币器节点处停止普通 BFS，不将混币后的地址强行认定为同一资金链。
- 风险实体标签库为项目内维护的演示数据集，不等同于商业 KYT 数据供应商的完整情报库。

## Repository

GitHub: https://github.com/dayaocc/kyt-lab

