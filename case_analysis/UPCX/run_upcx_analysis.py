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
    print("UPCX 真实安全事件风险分析启动")
    print("="*50)

    # 1.加载基础配置
    load_dotenv(dotenv_path="src/infrastructure/.env")
    api_key = os.getenv("ETHERSCAN_API_KEY")
    if not api_key:
        raise ValueError("请在 src/infrastructure/.env 中配置 ETHERSCAN_API_KEY")

    # UPCX 案件可疑的黑客初始地址
    TARGET_ADDRESS = "0x0DDC6030572Aa4B73EE82d6650cAc9B5cd5ffd00"

    # 2.装配数据获取层
    print("\n[1/5] 初始化数据获取层..")
    provider = EtherscanProvider(api_key=api_key)
    listener = ChainListener(
        provider=provider,
        normalizer_func=DataNormalizer.normalize_etherscan
    )

    # 3.装配TraceEngine
    trace_config = TraceConfig(
        target_address=TARGET_ADDRESS,
        direction="outflow",
        min_amount=0.0,
        max_depth=3,        
    )

    trace_engine = TraceEngine(
        listener=listener,
        config=trace_config
    )

    # 4.装配risk_engine
    print("[2/5] 挂载 风险检测插件...")
    peel_detector = PeelchainDetector(
        peel_min_ratio=0.01,
        peel_max_ratio=0.20,
        main_min_ratio=0.50,
        min_chain_length=3
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


    # 检查Detector
    print("\n===PeelChainDetector单独测试===")
    peel_alerts = peel_detector.detect(trace_tree)
    print(json.dumps(peel_alerts, indent=4, ensure_ascii=False))
    
    print("\n===SanctionDetector单独测试===")
    sanction_alerts = sanction_detector.detect(trace_tree)
    print(json.dumps(sanction_alerts, indent=4, ensure_ascii=False))

    
    # 7.风险分析
    print(f"\n[3/5] 开始执行风险分析 (目标: {TARGET_ADDRESS})...")
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
    result_dir = "case_analysis/UPCX/results"
    os.makedirs(result_dir, exist_ok=True)      # 创建文件夹
    result_path = os.path.join(result_dir, "analysis_result.json")

    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(analysis_result, f, indent=4, ensure_ascii=False)
    print(f"\n完整分析结果已保存到：{result_path}")   

    # 9.输出可视化图谱
    print("\n[4/5]生成交互式资金图谱...")

    graph_builder = GraphBuilder(output_dir=result_dir)

    graph_builder.build_from_trace(
        trace_tree=trace_tree,
        risk_profiles=risk_profiles,
        seed_address=TARGET_ADDRESS
    )

    graph_path = os.path.join(
        result_dir,
        "transaction_graph.html"
    )

    graph_builder.generate_interactive_html(
        output_filepath=graph_path
    )

    # 10.生成报告
    print("\n[5/5]自动生成调查报告....")
    report_gen = ReportGenerator(output_dir=result_dir)
    report_gen.generate_markdown(
        target_address=TARGET_ADDRESS,
        trace_tree=trace_tree,
        risk_profiles=risk_profiles,
        filename="upcx_investigation_report.md"
    )


    # 11.输出最终摘要
    print("\n" + "=" * 50)
    print("upcx案件分析完成")
    print(f"资金路径数量：{len(trace_tree)}")
    print(f"风险实体数量：{len(risk_profiles)}")
    print("=" * 50)
    print(f"JSON结果：{result_path}")
    print(f"资金流图谱：{graph_path}")
    print("=" * 50)
    

    return analysis_result

if __name__ == "__main__":
    main()





   

   


