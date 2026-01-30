
# 抓取1个以太坊区块的完整交易信息
# 1.导入翻译官,用一个叫 web3 的模块，从里面拿一个叫 Web3 的类
from web3 import Web3  
# 建立连接：把你的 Alchemy 地址放进去
# 这就像是给翻译官一个翻译机的地址
rpc_url = "https://eth-mainnet.g.alchemy.com/v2/rhOfO_G-zcxyYYX_HYPF0"
w3 = Web3(Web3.HTTPProvider(rpc_url))

# 2. 确认通话：看看有没有连上
if w3.is_connected():
    print("已经连上以太坊主网")

# 3. 拿区块信息
#  full_transactions=True：
#   - 如果为 False，你只能拿到一堆哈希值（ID）
#   - 如果为 True，你能拿到发送方、接收方、金额等完整“档案”
block = w3.eth.get_block('latest', full_transactions=True) # 拿到最新的区块信息

print(f"区块号:{block.number}")  # 打印区块号
tx_list = block['transactions']  # 拿到区块里的交易列表
print(f"这个区块包含{len(tx_list)}笔交易")  

# 4. 数据清洗
clean_data = [] # 准备一个空列表，用来装干净的交易档案
# for循环的方法，只适合对一个区块过滤，很慢
for tx in tx_list:
    # 提取我们关心的 4 个关键信息
    row = {
        "tx_hash": tx['hash'].hex(),  # 交易哈希值，转成16进制字符串
        "from": tx['from'],
        "to": tx['to'],
        "value": w3.from_wei(tx['value'], 'ether')  # 把 Wei 转成 Ether
    }
    clean_data.append(row)  # 那 append 一定在 for 里面,如果在外面，那你就只是在存「最后一个」
print(clean_data[0])  # 打印第一笔交易的干净档案
