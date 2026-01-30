from dotenv import load_dotenv

load_dotenv()  # 从.env 文件加载环境变量

# 数据库配置字典
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "password": os.getenv("DB_PASSWORD"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "port": os.getenv("DB_PORT")
}

# Telegram 机器人配置
# 全大写，表示是全局常量
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  #写入 发送方Telegram Bot 的 API Token，敏感信息，将存在.env 文件中
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")    #接收方Telegram 的 聊天 ID，敏感信息，将存在.env 文件中

# 运行配置
SCAN_INTERVAL = 600  # 扫描间隔，单位：600秒 (10分钟)