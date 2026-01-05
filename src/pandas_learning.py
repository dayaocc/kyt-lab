import pandas as pd

# 准备数据：一个包含字典的列表（每个 dict 是一行）
tx_list = [
    {"hash": "0x123", "from": "0xA", "to": "0xB", "value": 0.5},
    {"hash": "0x456", "from": "0xC", "to": "0xA", "value": 150.0},
    {"hash": "0x789", "from": "0xB", "to": "0xD", "value": 1.2},
]

# 1) 一键变表格
df = pd.DataFrame(tx_list)

print("=== DataFrame head() ===")
print(df.head())

print("\n=== 只看 from/to 两列 ===")
print(df[["from", "to"]])

print("\n=== value 这一列的统计 ===")
print(df["value"].describe())

# 2) mask：布尔开关（True/False），用于筛选行
mask = df["value"] > 100
big_tx = df[mask]  # 或 df[df["value"] > 100]

print("\n=== 大额交易（value > 100）===")
print(big_tx)

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
