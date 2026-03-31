from database import DatabaseManager
from config import DB_CONFIG

db = DatabaseManager(DB_CONFIG)     # 数据库连接
db.cur.execute("SELECT tx_hash, symbol, value, timestamp FROM transactions;")
print(db.cur.fetchall())
db.close()