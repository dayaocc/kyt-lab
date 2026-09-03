import os
import json
from dotenv import load_dotenv

# 导入数据层组件
from src.data_collection.providers.etherscan import EtherscanProvider
from src.data_collection.normalizer import DataNormalizer
from src.data_collection.chain_listener import ChainListener

# 导入风险分析层组件
from src.risk_analysis.detectors.sanction import SanctionDetector
from src.risk_analysis.detectors.peel_chain import PeelchainDetector
from src.risk_analysis.risk_engine import RiskEngine
from src.trace_engine.trace_engine import TraceEngine, TraceConfig

# 导入可视化组件
from src.visualization.graph_builder import GraphBuilder
from src.report.generator import ReportGenerator


def main():
    print("="*50)
    print("Harmony horizen Bridge真实安全事件风险分析启动")
    print("="*50)

    # 1.加载基础配置
    load_dotenv(dotenv_path="src/infrastructure/.env")

    api_key = os.getenv("ETHERSCAN_API_KEY")

    if not api_key:
        raise ValueError("请在 src/infrastructure/.env 中配置 ETHERSCAN_API_KEY")


    # 2.装配数据获取层
    print("\n[1/6] 初始化数据获取层..")
    provider = EtherscanProvider(api_key=api_key)

    listener = ChainListener(
        provider=provider,
        normalizer_func=DataNormalizer.normalize_etherscan        
    )
    
    HARMONY_START_BLOCK = provider.get_block_by_date(
            date_str="2022-06-23",
            closest="after"           
        )
    HARMONY_END_BLOCK = provider.get_block_by_date(
            date_str="2022-07-11",
            closest="before"             
        )

    # Harmony horizen 案件可疑的黑客初始地址
    HARMONY_TARGET_ADDRESS = (
        "0x0d043128146654c7683fbf30ac98d7b2285ded00"
    )

    HARMONY_MAX_DEPTH = 3
    
    print(
        f"Harmony调查区块范围：{HARMONY_START_BLOCK} → {HARMONY_END_BLOCK}"
    )

     # 3.装配TraceEngine
    print("\n[2/6] 配置深度追踪引擎(BFS)...")

    trace_config = TraceConfig(
        target_address=HARMONY_TARGET_ADDRESS,
        direction="outflow",
        min_amount=0.0,
        max_depth=HARMONY_MAX_DEPTH,
        start_block=HARMONY_START_BLOCK,
        end_block=HARMONY_END_BLOCK
    )

    trace_engine = TraceEngine(
        listener=listener,
        config=trace_config
    )

    # 4.装配risk_engine
    print("[3/6] 挂载AML风险检测插件...")

    peel_detector = PeelchainDetector(
        peel_min_ratio=0.01,
        peel_max_ratio=0.20,
        main_min_ratio=0.50,
        min_chain_length=3,
        max_step_drop_ratio=0.20
    )

    sanction_detector = SanctionDetector()  # 默认会自动读取 src/data/sanction_list.json

    # 5.依赖注入：将检测插件装配到主引擎
    risk_engine = RiskEngine(
        detectors=[
            peel_detector,
            sanction_detector
        ]
    )

    # 6.资金追踪
    trace_tree = trace_engine.start_tracing()
    
    if not trace_tree:
        print("未追踪到有效资金路径。")
        return
    
    print(f"\n资金追踪完成，共发现 {len(trace_tree)} 条有效资金路径。")

   
    # -----------临时调试=====Tornado Cash路径检查—-----------------
    # TORNADO_ROUTER = "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b"
    # TORNADO_T100 = "0xa160cdab225685da1d56aa342ad8841c3b53f291"

    # print("\n======Tornado Cash路径检查======")

    # for tx in trace_tree:
    #     from_addr = (tx.get('from') or "").lower()
    #     to_addr = (tx.get('to') or "").lower()

    #     amount = tx.get('amount', 0)
    #     symbol = tx.get('symbol', '')

    #     if (
    #         to_addr == TORNADO_ROUTER.lower() or
    #         to_addr == TORNADO_T100.lower()           
    #     ):
    #         print(
    #             f"[命中Tornado Cash路径]  "
    #             f"{from_addr} → {to_addr} "
    #             f"| {amount} {symbol}"                
    #         )

    #     elif (
    #         symbol == "ETH" and 99.9 <= amount <= 100.1           
    #     ):
    #         print(
    #             f"[100 ETH 候选路径]  "
    #             f"{from_addr} → {to_addr} "
    #             f"| {amount} {symbol}"                
    #         )

    #-----------临时调试=====Harmony 路径检查—-----------------
    # H5 = "0x4507ac1bdf4ae5e61ffcec3a9aeda312e2505970"
    # H6 = "0x432a9cb4353bed67ec5351734d4a44c0826847ae"
    # H7 = "0x8a0858888beeb5d1435ecd3657831699f169c3f4"

    # HARMONY_NEXT_HOPS = {H5, H6, H7}
    # print("\n======Harmony Horizen路径检查======")

    # for tx in trace_tree:
    #     from_addr = (tx.get('from') or "").lower()
    #     to_addr = (tx.get('to') or "").lower()

    #     amount = tx.get('amount', 0)
    #     symbol = tx.get('symbol', '')

    #     if to_addr in HARMONY_NEXT_HOPS:
    #         print(
    #             f"[命中Harmony Horizen路径]  "
    #             f"{from_addr} → {to_addr} "
    #             f"| {amount} {symbol}"                
    #         )



    # -------补充测验----检查Detector
    # print("\n===PeelChainDetector单独测试===")
    # peel_alerts = peel_detector.detect(trace_tree)
    # print(json.dumps(peel_alerts, indent=4, ensure_ascii=False))
    
    # print("\n===SanctionDetector单独测试===")
    # sanction_alerts = sanction_detector.detect(trace_tree)
    # print(json.dumps(sanction_alerts, indent=4, ensure_ascii=False))

    
    # 7.风险分析
    print(f"\n[4/6] 开始执行风险分析 (目标: {HARMONY_TARGET_ADDRESS})...")

    risk_profiles = risk_engine.run_analysis(
        trace_tree
    )

    print("\n" + "="*20 + " 风险实体画像 (Address Profiles) " + "="*20)

    if not risk_profiles:
        print("未检测到高危风险特征")
    else:
        print(json.dumps(risk_profiles, indent=4, ensure_ascii=False))

    analysis_result = {
        "trace_tree": trace_tree,
        "risk_profiles": risk_profiles
    }
    
    # 8.保存结果到文件中
    result_dir = "case_analysis/harmony_horizon/results"

    os.makedirs(result_dir, exist_ok=True)      # 创建文件夹

    result_path = os.path.join(result_dir, "analysis_result.json")

    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(analysis_result, f, indent=4, ensure_ascii=False)

    print(f"\n完整分析结果已保存到：{result_path}")   

    # 9.输出可视化图谱
    print("\n[5/6]生成交互式资金图谱...")

    graph_builder = GraphBuilder(output_dir=result_dir)

    graph_builder.build_from_trace(
        trace_tree=trace_tree,
        risk_profiles=risk_profiles,
        seed_address=HARMONY_TARGET_ADDRESS
    )

    graph_path = os.path.join(
        result_dir,
        "transaction_graph.html"
    )

    graph_builder.generate_interactive_html(
        output_filepath=graph_path
    )

  

    # 10.生成报告
    print("\n[6/6]自动生成调查报告....")

    report_gen = ReportGenerator(output_dir=result_dir)

    report_gen.generate_markdown(
        target_address=HARMONY_TARGET_ADDRESS,
        trace_tree=trace_tree,
        risk_profiles=risk_profiles,
        filename="harmony_investigation_report.md"
    )


    # 11.输出最终摘要
    print("\n" + "=" * 50)
    print("harmony_horizen案件分析完成")
    print(f"资金路径数量：{len(trace_tree)}")
    print(f"风险实体数量：{len(risk_profiles)}")
    print("=" * 50)
    print(f"JSON结果：{result_path}")
    print(f"资金流图谱：{graph_path}")
    print("=" * 50)    

    return analysis_result

if __name__ == "__main__":
    main()





   

   


