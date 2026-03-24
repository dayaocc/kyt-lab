import psycopg2
import os
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_config):  # db_config是一个字典，包含连接数据库所需的信息
        self.conn = psycopg2.connect(**db_config)   # **把一个字典里面的“键值对”，打散成一个个**关键字参数,传递给函数
        self.cur = self.conn.cursor()
        # # 以当前文件为基准定位 sql 目录
        base_dir = Path(__file__).resolve().parent
        self.sql_path = base_dir / "sql"

    def _load_sql(self, filename):
        # 内部方法：加载 SQL 文件内容
        full_path = self.sql_path / filename
        with open(full_path, 'r') as file:
            sql = file.read()
        return sql

    def create_tables(self):
        # 加载建表语句
        create_sql = self._load_sql("create_tables.sql")
        try:
            self.cur.execute(create_sql)  # 执行建表语句
            # 这里的 commit 必须立刻执行，确保表结构被物理写入硬盘
            self.conn.commit()  
            print("数据表结构初始化成功，档案库已扩容")
        except Exception as e:
            print(f"建表失败：{e}")
            self.conn.rollback()  # 回滚事务，防止半成品数据留在数据库中    

    # 将清洗后的交易数据写入数据库
    def insert_transaction(self, tx_data):  
        insert_sql = self._load_sql("insert_transaction.sql")
        # 按照 SQL 语句中 %s 的顺序,所有参数必须以序列形式传入，所以将数据做成元组
        params = (
            tx_data.get('tx_hash'),
            tx_data.get('from'),
            tx_data.get('to'),
            tx_data.get('amount', 0),    # 对应 value 列，查找amount键。如果没有对应的key，金额默认存 0
            tx_data.get('input_data'),
            tx_data.get('block_number', 0),
            tx_data.get('timestamp'),
            tx_data.get('type', 'UNKNOWN'),
            tx_data.get('token_address'),
            tx_data.get('symbol')
        )
        try:
            self.cur.execute(insert_sql, params)    # 让外面（比如 main.py）循环完 100 次后再统一 commit，速度会快几十倍。
            return True   # 成功时，返回 True
        except Exception as e:
            print(f"插入数据时发生错误(Hash: {tx_data.get('tx_hash')}): {e}")
            self.conn.rollback()    # 如果某一条出错，立刻回滚当前事务，保护数据库安全
            return False  # 失败时，返回 False

        

    # 刷新高危风险视图
    def refresh_risk_views(self):
        refresh_query = self._load_sql("refresh_risk_view.sql")
        self.cur.execute(refresh_query)
        # self.conn.commit()    #防止网络中断出现报批和实际数据不相符的情况发生，需要在调用此方法后手动提交事务

    # 抓取未报告的高危交易
    def fetch_new_alerts(self):
        #使用辅助方法加载 SQL;        
        fetch_query = self._load_sql("fetch_new_alerts.sql")
        self.cur.execute(fetch_query)
        return self.cur.fetchall()  # 返回所有查询结果
    
    # 更新数据库状态，标记已读，防止重复报警
    def mark_as_reported(self,tx_hash):
        update_sql_query = self._load_sql("mark_as_reported.sql")
        self.cur.execute(update_sql_query, (tx_hash,)) # 单元素元组    



    # 统一提交事务
    def commit(self):
        self.conn.commit()  # 方便手动提交当前事务，把游标执行的操作“写入数据库”

    # 关闭数据库连接
    def close(self):
        self.cur.close()    # 关闭游标
        self.conn.close()   # 关闭连接通道.一旦 conn 关闭，所有依附于它的 cur 都会自动失效并关闭
    
if __name__ == "__main__":
    from config import DB_CONFIG
    db = DatabaseManager(DB_CONFIG)     # 数据库连接
    db.create_tables()                  # 创建表
    db.close()                      # 关闭连接