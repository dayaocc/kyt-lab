# 用pandas做数据清洗
import pandas as pd  # 习惯我们把 pandas 简写为 pd
# 准备数据：一个包含字典的列表
tx_list = [
    {"hash": "0x123", "from": "0xA", "to": "0xB", "value": 0.5},
    {"hash": "0x456", "from": "0xC", "to": "0xA", "value": 150.0},
    {"hash": "0x789", "from": "0xB", "to": "0xD", "value": 1.2}
]
# 一键变表格：pd.DataFrame--调用 pandas 的 DataFrame 构造器，把数据变成“表格对象”,自动根据字典里的键值生成表格的内容
# 键值会自动充当列名
df = pd.DataFrame(tx_list)
# 查看表格的前几行  .head()：DataFrame 的方法，返回前 N 行（默认 5 行）
print(df)
print(df.head())

print(df['value'])  # 看某一列
print(df[['from', 'to']]) #看多列，里面的[]是表示 列名的列表
print(df.head(2)) # 看前2行
print(df.describe()) # 看统计摘要




# 2) mask：布尔开关（True/False），用于筛选行.逻辑判断语句，所以mask是个布尔值序列
mask = df["value"] > 100
# 布尔索引。
big_tx = df[mask]  # 或 df[df["value"] > 100]

print("\n=== 大额交易（value > 100）名单===")
print(big_tx)
print("\n=== 目标大额交易名单===")
targe_tx = df[(df['value'] > 1) & (df['to'] == '0xB')]
print(targe_tx)


'''
# 3) 加一列风险评级（示范：黑名单 or 大额）
blacklist = {"0xA", "0x999"}

def analyze_row(tx):
    if tx["from"] in blacklist or tx["to"] in blacklist:
        return "High"
    elif tx["value"] > 100:
        return "Medium"
    else:
        return "Low"

df["risk_level"] = df.apply(analyze_row, axis=1)

print("\n=== 加上 risk_level 后 ===")
print(df)
'''
# 3) 筛选更复杂的条件行
blacklist = {"0xA", "0xB", "0x999", "0x777"}
# 条件1：df['is_risky'] == True
# is_risky = (df['from'] == "0xA") | (df['to'] == "0xA")

# 检查 'from' 和 'to' 这二列的每个值，是否在 blacklist 这个列表里
is_risky = df['from'].isin(blacklist) | df['to'].isin(blacklist)
# 条件2：df['value'] > 50
is_large = df['value'] > 50
# 连接符：& (代表“且”).上面is_risky 和 is_large 都是布尔值序列
danger_zone = df[is_large & is_risky]
# 
clean_tx = df[~df['from'].isin(blacklist) & ~df['to'].isin(blacklist)]


print("\n=== 诡异危险交易筛选名单 ===")
blacklist = {"0xA", "0xB", "0x999", "0x777"}  # 集合查找，更快
blacklist_lower = {str(x).lower() for x in blacklist}  # 全部变小写
# 为了防止错漏，分不清大小写。检查地址，将地址全部变为小写
df['from'] = df['from'].str.lower()
df['to'] = df['to'].str.lower()

is_risky = df['from'].isin(blacklist_lower)
half_risky = ~df['to'].isin(blacklist_lower)
is_large = df['value'] > 100
danger_zone = df[is_large & is_risky & half_risky]
print(danger_zone)

print("\n=== 杜绝分次转账式的洗钱手法 ===")
# 第一步：算出每个地址的总转账额
total_volumes = df.groupby('from',as_index=False)['value'].sum()    #as_index=False表示 “from 不要当 index，当普通列”
# 第二步：重命名列名，让它更好理解 (把 'value' 改成 'total_spent')
total_volumes.columns = ['address', 'total_spent']
# 第三步：整体过滤，找出累计转账超过 100 ETH 的“隐形大户”
smurfing_suspects = total_volumes[total_volumes['total_spent'] > 100]
# 第四步：展示结果
print("\n=== 累计转账超限嫌疑人名单： ===")
print(smurfing_suspects)
# 分组函数grouby：按 from 分组，对 value 计算 count
total_counts = df.groupby('from',as_index=False)['value'].count()


# # 一键生成风险画像：按 from 分组，对 value 同时计算 sum 和 count
risk_profile = df.groupby('from',as_index=False)['value'].agg(['sum','count'])
# 为了方便阅读，我们重命名一下表头
risk_profile.columns = ['address', 'total_spent', 'tx_count']
# 筛选：总额 > 100 且 次数 > 50 的极端嫌疑人
super_sespects = risk_profile[(risk_profile['total_spent'] > 100) & (risk_profile['tx_count'] > 50)]


import pandas as pd
# 1. 模拟把数据变成一张大表
df = pd.DataFrame(tx_list)

# 2. 整体过滤：直接筛选出金额 > 100 的所有行
# 这就是你想要的“整体过滤条件”！
big_transfers = df[df['value'] > 100]
# 3. 整体标记：如果 sending 地址在黑名单里，全表对应的风险列瞬间变 High
df.loc[df['from'].isin(blacklist), 'risk_level'] = 'High'