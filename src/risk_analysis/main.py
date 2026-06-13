from peel_chain_detector import PeelchainDetector

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

    # 2.分析交易数据，识别剥皮链和自动化打散
    detector = PeelchainDetector()
    print("开始审查资金链路，识别剥皮链和自动化打散行为...")
    reports  = detector.detect(mock_trace_tree)

    #3.输出分析报告
    print("\n 发现高危风险事件：")
    for idx, report in enumerate(reports, 1):  #遍历，同时使用enumerate()函数获取索引和报告内容，并从1开始编号
        print(f"[{idx}] 嫌疑人：{report['sender']}, 风险标签：{report['label']}, 评分：{report['score']}")
        if 'path_amounts' in report:
            print(f"  犯罪轨迹（大额流转）： {report['path_amounts']}")
        if 'amounts' in report:
            print(f"  打散金额：{report['amounts']}")
        print("-"*50)

    print(f"审查完毕，共生成{len(reports)}份风险报告。正常用户未触发警报。")

if __name__ == "__main__":
    main()