import psycopg2
# 建立连接
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="kytlab",
    user="kytuser",
    password="SuperSecret123"
)
# 创建一个“游标”来执行 SQL
cur = conn.cursor()
cur.execute("SELECT 1;")
print(cur.fetchone())

cur.close()
conn.close()
