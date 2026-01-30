# 导入写好的工具类
# from database_manager import DatabaseManager
import time
from datetime import date
from config import DB_CONFIG, TELEGRAM_BOT_TOKEN, CHAT_ID, SCAN_INTERVAL
from datebase import DatabaseManager
from notifier import TelegramBot
from reporter import RiskReporter
def main()
    # 1.实例化所有工具
    db = DatabaseManager(DB_CONFIG)
    bot = TelegramBot(TELEGRAM_BOT_TOKEN, CHAT_ID)
    reporter = RiskReporter()
    print("自动化风险监控程序已启动...")

    while True:
        try:
            # 2.抓取数据
            alerts = db.fetch_new_clerts()
