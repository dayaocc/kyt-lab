import psycopg2
import os

class DatabaseManager:
    def __init__(self, db_config):  # db_config是一个字典，包含连接数据库所需的信息
        self.conn = psycopg2.connect(**db_config)   # **把一个字典里面的“键值对”，打散成一个个**关键字参数,传递给函数
        self.cur = self.conn.cursor()
        # 定义SQL 文件存放的基准路径
        self.sql_path = "src/scripts/sql/"
    
    def _load_sql(self, filename):
        # 内部方法：加载 SQL 文件内容
        full_path = os.path.join(self.sql_path, filename)
        with open(full_path, 'r') as file:
            sql = file.read()
        return sql

    # 刷新高危风险视图
    def refresh_risk_views(self):
        query = self._load_sql("refresh_risk_view.sql")
        self.cur.execute(query)
        # self.conn.commit()    #防止网络中断出现报批和实际数据不相符的情况发生，需要在调用此方法后手动提交事务

    # 抓取未报告的高危交易
    def fetch_new_alerts(self):
        #使用辅助方法加载 SQL;        
        query = self._load_sql("fetch_new_alerts.sql")
        self.cur.execute(query)
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