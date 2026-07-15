from risk_analysis.peel_chain_detector import PeelchainDetector
from risk_analysis.sanction_screener import SanctionScreener
from risk_analysis.risk_engine import RiskEngine
from visualization.graph_builder import GraphBuilder


def main():
    print("KYT 智能风控系统 正在启动...")

    # 1.捏造假数据 （模拟TraceEngine 抓取到的数据结构）
    mock_trace_tree = [
        # ---A：动态剥皮链 (Dynamic Peel Chain)---
        # 初始总资金：10000 (转出 9500 大头，剥离 500)
        {'from': '0x黑客首脑', 'to': '0x中转钱包A', 'amount': 9500, 'current_depth': 0},
        {'from': '0x黑客首脑', 'to': '0x套现地址1', 'amount': 500, 'current_depth': 0},

        #中转A 继续剥皮 (转出 9100 大头，剥离 400)
        {'from': '0x中转钱包A', 'to': '0x中转钱包B', 'amount': 9100, 'current_depth': 1},
        {'from': '0x中转钱包A', 'to': '0x套现地址2', 'amount': 400, 'current_depth': 1},

        #中转B 继续剥皮 (转出 8800 大头，剥离 300)
        {'from': '0x中转钱包B', 'to': '0x最终沉淀池', 'amount': 8800, 'current_depth': 2},
        {'from': '0x中转钱包B', 'to': '0x套现地址3', 'amount': 300, 'current_depth': 2},

        #----B：自动化打散 (Automated Fan-out)----
        # 机器脚本连续发送 4 笔相同金额
        {'from': '0x发币脚本', 'to': '0x羊毛党1', 'amount': 1000, 'current_depth': 0},
        {'from': '0x发币脚本', 'to': '0x羊毛党2', 'amount': 1000, 'current_depth': 0},
        {'from': '0x发币脚本', 'to': '0x羊毛党3', 'amount': 1000, 'current_depth': 0},
        {'from': '0x发币脚本', 'to': '0x羊毛党4', 'amount': 1000, 'current_depth': 0},

        #----C：正常的普通用户 (作为噪音干扰，看系统会不会误报)-----
        {'from': '0x正常人', 'to': '0x朋友A', 'amount': 50, 'current_depth': 0},
        {'from': '0x正常人', 'to': '0x餐厅老板', 'amount': 120, 'current_depth': 0},
    ]

    print(f"成功抓取{len(mock_trace_tree)}笔链上交易数据，正在分析中...")

    # 建立用于收集所有警报的总清单
    all_risk_reports = []       # list

    # 2.检查制裁名单，扫描所有出现的地址。
    print("启动制裁名单 API 碰撞测试。。。")
    screener = SanctionScreener(use_mock=True)  # 使用模拟API


    # 提取所有出现过的独立地址 (去重)
    all_addresses = set([tx['from'] for tx in mock_trace_tree] + [tx['to'] for tx in mock_trace_tree])  
    
    for addr in all_addresses:
        scanction_report = screener.check_address(addr)  # 检查每个地址是否在制裁名单中
        if scanction_report:
            all_risk_reports.append(scanction_report)  # 如果命中制裁名单，则加入总风险报告清单
            print(f"[制裁名单警报] 地址 {addr} 命中制裁名单，已生成风险报告。")

    
    # 3.分析交易数据，识别剥皮链和自动化打散
    print("启动剥皮链和自动化打散行为检测...")
    peel_detector = PeelchainDetector()
    print("开始审查资金链路，识别剥皮链和自动化打散行为...")
    behavior_reports  = peel_detector.detect(mock_trace_tree)
    all_risk_reports.extend(behavior_reports)  # 将行为分析报告加入总风险报告清单

    # 4.综合评分评估，输出分析报告
    print("[Risk Engine] 正在进行实体融合与综合定级...")
    engine = RiskEngine()
    final_profiles = engine.generate_comprehensive_profiles(all_risk_reports)
        
    for address, profile in final_profiles.items():  #遍历，同时使用enumerate()函数获取索引和报告内容，并从1开始编号
        print(f"""
            嫌疑主体：{profile['address']} 
            风险标签：{profile['labels']}（共触发{profile['violation_count']}项规则）
            最终风险评分：{profile['final_score']}/100
            风险等级：{profile['risk_level']}
            """)
        
        if profile['evidence']:
            print("  证据详情：")
            for evidence in profile['evidence']:
                print(f"    - {evidence}")
        

        print("-"*50)

    print("正在生成本地关系图谱...")
    builder = GraphBuilder()
    builder.build_from_trace(mock_trace_tree)
    builder.visualize()  
# =================测试代码=================

if __name__ == "__main__":
   
    main()