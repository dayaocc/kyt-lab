import os
from dotenv import load_dotenv
import psycopg2
import time
import requests
import pandas as pd
from datetime import date
import matplotlib.pyplot as plt     # 引入可视化工具matlib
import seaborn as sns       # 让图表更美观的seaborn

load_dotenv()  # 从.env 文件加载环境变量


# 从环境变量中读取，而不是写死在代码里.
conn = psycopg2.connect(        # 建立与数据库之间的连接管道
    host=os.getenv("DB_HOST"),
    password=os.getenv("DB_PASSWORD"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    port=os.getenv("DB_PORT") 
)
cur = conn.cursor()  # 向数据库“借一个操作指针（游标)

 # 模块：用telegram机器人API发送文字消息
def send_telegram_msg(text):
    token = os.getenv("TELEGRAM_BOT_TOKEN")  #写入 发送方Telegram Bot 的 API Token，敏感信息，将存在.env 文件中
    chat_id = os.getenv("TELEGRAM_CHAT_ID")    #接收方Telegram 的 聊天 ID，敏感信息，将存在.env 文件中
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    # 发送http请求
    requests.post(url, data=payload)        #目标地址, 请求数据

# 模块：用telegram机器人发送图片
def send_telegram_photo(caption, image_path)
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendPhoto"

    # 1. 以二进制读取模式 ('rb') 打开图片文件
    # Python 处理文件最推荐的方式,with..as..,能确保文件在使用完后自动关闭
    with open(image_path, 'rb') as img_file:    # r 读取模式，b 二进制模式
        # 2. 构建请求数据
        # 'photo' 是 Telegram API 要求的参数名
        files = {'photo': img_file}     # 要上传的文件流
        data = {'chat_id': chat_id, 'caption': caption} #这是随文件发送的文本元数据; caption 是图片的文字说明
        # 3. 发送 POST 请求，包含文件数据；POST 通常用于向服务器提交数据
        requests.post(url, data=data, files=files)  
        print("图片汇总已推送到 Telegram")



# 自动化运行：只要程序没被强行关闭，就一直运行下去
while True:
    try:
        # 1. 刷新我们在 SQL 模块建立的“照片”
        refresh_query = "REFRESH MATERIALIZED VIEW high_risk_snapshot;"   # Materialized View = 存结果的“快照表”
        # 2. 查询发现未报警过的高危名单
        select_query = "SELECT * FROM high_risk_snapshot WHERE total_risk_score >= 80 AND is_reported = FALSE;" 

        cur.execute(refresh_query)  # 执行刷新快照表的命令.调用游标的执行方法，把 SQL 语句发给数据库PostgreSQL
        conn.commit()  # 确认刷新： 提交当前事务，把游标执行的操作“写入数据库”

        cur.execute(select_query)  # 执行查询命令
        # 获取所有查询结果
        alerts = cur.fetchall()  # 这一步会把所有符合条件的行拿回到 Python 变量里
        today = date.today()
        all_alerts_data = []    # 准备空列表存放所有风险数据
        # 检查是否有高危记录
        if alerts:
            # 增加处理报警消息
            for row in alerts:
                current_tx = row[0]
                # 1. 先发telegram消息报警
                send_telegram_msg(f"发现高危交易：{current_tx}")
                # 2. 紧接着更新数据库状态，防止重复报警
                update_sql = "UPDATE risk_alerts SET is_reporeted = TRUE WHERE tx_hash = %s;"    # 使用 %s 占位符是防止 SQL 注入的专业写法
                cur.execute(update_sql, (current_tx,))  # 单元素元组的表示方法
                conn.commit()  # 提交更新操作,让修改永久生效
                print(f"警报！发现{len(alerts)}条高危记录")
                
                
                # 3.把每一行数据装进篮子
                all_alerts_data.append({
                'transaction_hash': row[0],
                'eth_value': row[1],
                'sender': row[2],
                'risk_level': 'High'
                })  
            # 当循环结束（篮子装满了），再执行导出
            if all_alerts_data:
                df = pd.DataFrame(all_alerts_data)

                level_counts = df['risk_level'].value_counts()
                print("--风险等级分布--")
                print(level_counts)
                # 深度汇总：每个等级有多少笔，以及涉及的总金额是多少？
                summary_report = df.grounpby('risk_level').agg({
                    'transaction_hash': 'count',    #计算笔数
                    'value_usd': 'sum'      #计算总金额
                }).rename(columns={'transaction_hash': '交易笔数', 'value_usd': '涉及金额(USD)'})
                print("\n--合规汇总日报--")
                print(summary_report)

                #excel分析
                df.to_excel(f"risk_report_{today}.xlsx", index=False)  
                #可视化展现  
                send_telegram_photo(
                    caption=f"【每日合规简报】\n 日期：{today} \n 请审阅今日高风险交易趋势图。"
                    image_path=summary_report
                )                 
                
        else:
            print("巡检完毕，暂未发现高危风险。")
    
    except Exception as e:
        print(f"巡检中途遇到故障: {e}")
        print("系统将尝试在下轮循环中恢复。")
    
    print("等待下一次巡检。。。")
    time.sleep(600)  # 等待10分钟（600秒）后继续下一次巡检
        




# 模块：将返回数据转化为 Pandas 表格
column_names = ['transaction_hash', 'eth_value', 'entity_name']     #定义列名
df = pd.DataFrame(alerts, columns=column_names)     # 转化为DataFrame
print(df)  
total_amount = df['eth_value'].sum()    # 能算出这批高危交易的总金额

# 假设 eth_price 是从 API 获取的实时价格，这里我们定为 2500
eth_price = 2500    
# 直接对整列进行运算
df['balue_usd'] = df['eth_value'] * eth_price
print(df[['transaction_hash', 'eth_value', 'value_usd']])   # 一次选多列，用[]包起来




# 模块：获取今天的日期
today = date.today()
print(today)
filename = f"risk_report_{today}.xlsx"
df.to_excel("{filename}", index=FALSE)


# 模块：快速查看每个风险等级的笔数
level_counts = df['risk_level'].value_counts()
print("--风险等级分布--")
print(level_counts)
# 深度汇总：每个等级有多少笔，以及涉及的总金额是多少？
summary_report = df.grounpby('risk_level').agg({
    'transaction_hash': 'count',    #计算笔数
    'value_usd': 'sum'      #计算总金额
}).rename(columns={'transaction_hash': '交易笔数', 'value_usd': '涉及金额(USD)'})
print("\n--合规汇总日报--")
print(summary_report)



# 模块：可视化绘图代码
plt.figure(figsize=(8, 5))  #设置画布大小
# 2. 使用 Seaborn 绘制柱状图
# x轴放风险等级，y轴放总金额，根据不同的风险等级配不同的颜色

# seaborn绘制 柱状图 的核心函数barplot
chart = sns.barplot(
    data=summary_report.reset_index(),  # 重置索引，让 risk_level 变成普通列方便绘图
    x='risk_level',
    y='涉及金额(USD)',
    palette='viridis'   # 选择一个专业的配色方案
)
# 3. 添加标题和标签，让图表能“自解释”
plt.title(f"今日高危交易汇总{today}", fontsize=14)   # 把图表标题的字，设为 14 号字
plt.ylabel("涉及总金额(USD)", fontsize=12)
plt.xlabel("风险等级", fontsize=12)

chart_filename = f"risk_chart_{today}.png"
plt.savefig(chart_filename, dpi=100, bbox_inches='tight')   # 保存图表到指定路径，设置分辨率为100dpi，bbox_inches='tight'表示去掉多余白边
plt.close()
print(f"风险趋势图已生成：{chart_filename}")








   




