# 导入写好的工具类

import time
from datetime import date
from config import DB_CONFIG, TELEGRAM_BOT_TOKEN, CHAT_ID, SCAN_INTERVAL
from datebase import DatabaseManager
from notifier import TelegramBot
from reporter import RiskReporter
import pandas as pd
# 主程序入口函数
def main():
    # 实例化所有工具
    db = DatabaseManager(DB_CONFIG)
    bot = TelegramBot(TELEGRAM_BOT_TOKEN, CHAT_ID)
    reporter = RiskReporter()
    print("自动化风险监控程序已启动...")

    while True:
        try:
            # 1.刷新视图
            db.refresh_risk_views()

            # 2.抓取未报警的危险高危数据
            alerts = db.fetch_new_alerts()

            if alerts:
                print(f"发现 {len(alerts)} 条新高危记录")

                # 3.处理每笔交易
                for tx in alerts:
                    tx_hash = tx[0]
                    bot.send_telegram_msg(f"发现高危交易预警:{tx_hash}")
                    db.mark_as_reported(tx_hash)

                # 4.统一提交事务给数据库
                db.commit()

                # 5.生成并发送风险报告
                df = reporter.create_dataframe(alerts)
                chart_path = reporter.draw_risk_chart(df)
                excel_path = reporter.save_excel(df, f"{date.today()}风险汇总简报.xlsx")
                print("风险图表已生成")

                # 6.发送汇总图到 Telegram
                bot.send_telegram_photo(f"今日风险汇总报告: {date.today()}", chart_path)
                print("风险报告已发送到 Telegram")

            else:
                print("暂无新风险交易记录")

        except Exception as e:
            print(f"程序运行中遇到错误: {e}")
            print("系统将在下次循环时尝试恢复...")

        # 7.休息一下，等待下次扫描
        time.sleep(600)  # 暂停10分钟后继续下一轮巡检
    
# __main__代表“这是主程序/直接运行的文件”.整个if结构是区分“执行环境”和“导入环境”的防火墙，是入口判断。
# 运行这个文件时，程序从这里开始执行，方便文件测试.
# 如果这个文件被导入到其他文件中运行，下面的代码不会被执行。
if __name__ == "__main__":  
    main()      # 调用主函数
                

