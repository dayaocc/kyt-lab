from web3 import Web3

rpc_url = "https://eth-mainnet.g.alchemy.com/v2/rhOfO_G-zcxyYYX_HYPF0"
w3 = Web3(Web3.HTTPProvider(rpc_url))

if w3.is_connected():
    print("已经连上以太坊主网")
# 1. 获取当前最新区块号
latest_height = w3.eth.get_block_number()
print(f"最新区块高度是: {latest_height}")
# 2. 计算起点（抓取最近的 10 个块）
start_height = latest_height - 9

# 3. 准备一个大列表，装下所有块的交易
all_blocks_txs = [] 
print(f"开始抓取从{start_height}到{latest_height}的区块...")

# 4. 开始循环
for i in range(start_height, latest_height + 1):

    # 根据块号 i 抓取数据
    block = w3.eth.get_block(i, full_transactions=True)

    # 将该块的交易列表合并到我们的总表里

    all_blocks_txs.extend(block['transactions'])   

    print(f"已抓取到区块{i}, 目前累计交易数为{len(all_blocks_txs)}")


# 5. 数据清洗：提取我们关心的字段   

'''
import pandas as pd
df = pd.DataFrame(all_blocks_txs)

# 把列表中的 value 转换单位ether。用到apply()方法
df["value"] = df["value"].apply(lambda x: w3.from_wei(x, 'ether'))

# 筛选出金额大于50的交易
large_txs = df[df["value"] > 50]
print(f"在区块{start_height}到{latest_height}之间，金额大于50的交易有：")
print(large_txs)

# 上面代码返回的是完整的交易信息，所有行字段的“并集” = 所有列某一行没有的字段 → NaN, 拿了太多的字段。
接下来要进行数据清洗，只拿需要的字段，进行字段裁剪
'''
import pandas as pd
clean_rows = []
for tx in all_blocks_txs:
    row = {
        "tx_hash": tx['hash'].hex(),
        "from": tx['from'],
        "to": tx['to'],
        "value": w3.from_wei(tx['value'], 'ether'),
        # "gas": tx['gas'],
        # "tx_type": tx['type'],
        # "tx_index": tx["transactionIndex"]
    }
    clean_rows.append(row)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.width', None)
df = pd.DataFrame(clean_rows)
print("value最大值:", df["value"].max())
# 筛选出金额大于50的交易
large_txs = df[df["value"] > 50]
# 展示结果
cols = ["value", "tx_hash", "from", "to"]    # 把value列移到前面,列表定义，cols可以叫别的名字

print(f"在区块{start_height}到{latest_height}之间，金额大于50的交易有：")
print(large_txs[cols])
# print(large_txs)


'''
print(df.columns)   # 查看有哪些列
print(large_txs['value'])   # 只看 value 列
'''

# 6.数据富化,为存入Postgres数据库做准备
from datetime import datetime
# 我们先给筛选出来的“大鱼”表做个备份，避免干扰原数据
large_txs = large_txs.copy()    # .copy() 是为了确保我们是在一张新表上操作
# 1. 添加风险标记
print("开始进行数据富化...")
large_txs['risk_level'] = 'High'
# 2. 添加抓取时间
large_txs['scanned_at'] = datetime.now()
# 3. 添加规则说明
large_txs['rule_name'] = 'Amount > 50 ETH'
print(large_txs)


# 7.数据入库
from sqlalchemy import create_engine
from sqlalchemy.types import Numeric  # 用于指定数值类型
from decimal import Decimal
large_txs['value'] = large_txs['value'].apply(lambda x: Decimal(str(x)))  # 转换为 Decimal 类型
# 创建数据库连接引擎
# 就像建立了一个长期有效的“地下传输管道”
connection_string = "postgresql://kytuser:SuperSecret123@localhost:5432/kytlab"
engine = create_engine(connection_string)
# 将数据写入 Postgres 数据库。用 SQLAlchemy 将结果永久固化。
# 这一行代码会帮你完成：建表、对应字段、插入数据的所有工作
large_txs = large_txs.rename(columns={
    'from': 'from_address',
    'to': 'to_address'
})
print(large_txs.columns)

large_txs.to_sql(
    name='risk_alerts',     # 数据库里的表名
    con=engine,     # 使用我们刚才创建的管道
    if_exists='append', # # 如果表已经存在，就往后追加（增量同步的关键！）
    index=False,     # 不把 Pandas 的行号存进去
    dtype={
        'value': Numeric(20, 6)   # 指定 value 列的类型为数值型，保留6位小数
    }
)
print("数据已成功写入 Postgres 数据库的 risk_alerts 表中。")

# 8. 数据验证：从数据库里再读出来看看,用SQL查询语句
 # value::numeric = 告诉 Postgres：把 text 当数字用
query = """
SELECT 
    value, 
    risk_level,
    from_address,
    to_address,
    CASE
       WHEN value > 200 THEN 'Critical: Immediate Action'
       WHEN value> 50 THEN 'High: Review Required'
       ELSE 'Normal'
    END AS risk_assessment 
FROM risk_alerts
WHERE value > 50   
ORDER BY scanned_at DESC;
"""

result_df = pd.read_sql(query, engine)  # 从数据库里读数据进来,放到 Pandas 里,变成一个新的 DataFrame,叫 result_df.方便校验
print("查询到的高风险交易报告：")
print(result_df)

query = """
SELECT
    risk_level,
    COUNT(*) AS alert_count,
    SUM(value) AS total_value
FROM risk_alerts
WHERE scanned_at >= NOW() - INTERVAL '24 hours'   
GROUP BY risk_level;
"""
df_macro = pd.read_sql(query, engine)
print(df_macro)




