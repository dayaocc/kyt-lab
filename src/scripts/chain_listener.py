from database import DatabaseManager
from web3 import Web3
from config import ALCHEMY_RPC_URL, DB_CONFIG
import json
from datetime import datetime, timezone

# 定义一个最小化的 ERC20 ABI，只包含我们关心的 transfer 和 decimals(默认，小数位函数)
# 把 JSON 字符串 → Python 对象.type(ERC20_ABI) == list,里面每一项是一个 dict，描述一个函数.
ERC20_ABI = json.loads('''[
        {
            "constant": false, 
            "inputs": [
                {"name": "_to", "type": "address"},
                {"name": "_value", "type": "uint256"}
            ],
            "name": "transfer",
            "outputs": [{"name": "", "type": "bool"}],
            "type": "function"
        },
        {
            "constant": true,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "type": "function"
        },
        {
            "constant": true,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "type": "function"
        }
]''')

class ChainListener:
    def __init__(self, db_manager=None):    # db_manager=None外部传进来的数据库对象，设置默认值为None
        # 初始化连接：Web3 类 + HTTPProvider
        self.w3 = Web3(Web3.HTTPProvider(ALCHEMY_RPC_URL))
        self.db = db_manager    # 把外部传进来的数据库管理器赋值给了 ChainListener 的一个实例属性 self.db

    # 这是一个测试函数，用来确认握手是否成功
    def simple_check(self):        
        if self.w3.is_connected():
            print(f"已经连上以太坊主网，当前区块高度为：{self.w3.eth.block_number}")
            return True
        else:
            print("连接失败，请检查 URL 或网络。")
            return False
    
    # 输入input哈希字段，程序自动判断它是ETH“直汇”还是ERC20“合约调用”
    def decode_transaction(self, tx_hash):
        # 1.从链上抓取交易原始数据
        try:
            tx = self.w3.eth.get_transaction(tx_hash)   # 从交易id  tx_hash中查交易,返回tx是一个web3.datastructures.AttributeDict，本质行为 =  dict
                                  
       
        except Exception as e:
            return {"error":f"找不到交易或网络错误：{e}"}

        '''
        print(type(tx_hash))        # str
        print(type(tx))             # web3.datastructures.AttributeDict        
        print(type(tx['input']))    # HexBytes
        '''
        # 2.获取交易所在区块的详细信息
        block_number = tx.get('blockNumber')  
        real_time = None

        if block_number:
            try:
                # 调取整个区块的信息,时间在区块里而不是交易里
                block_info = self.w3.eth.get_block(block_number)
                # 提取 Unix 时间戳，并翻译成人类可读的格式
                unix_timestamp = block_info.get('timestamp')
                real_time = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)  # 采用UTC时间
            except Exception as e:
                print(f"获取区块信息失败: {e}")
        
        # 3.提取tx中的 input 数据 (有些版本叫 input，有些叫 data),即合约中的calldata               
        
        raw_input = tx.get('input', '0x')   # 如果input没有数据，就返回0x作为默认值
        # w3.to_hex() 将数据统一格式化为带 0x 前缀的 Hex string字符串（注意：是 HexBytes字节转化为字符串，便于同类型数据判断比较）
        input_data = self.w3.to_hex(raw_input)        
        
        # 4.逻辑分流：区分 ETH 和 ERC20
        # 绝大多数普通转账（EOA 到 EOA）的 input_data 都是空的（在浏览器上显示为 0x）        
        if input_data == '0x' or input_data == '0x0':   
        # === 情况 A: 原生 ETH 转账 ===
        # 金额在 value 字段，单位是 Wei，需要除以 10^18 换算成 ETH
            amount_eth = self.w3.from_wei(tx['value'], 'ether')
            return {
                "tx_hash": tx_hash,
                "type": "ETH_TRANSFER",
                "from": tx['from'],
                "to": tx['to'],
                "amount": float(amount_eth),    # 转换为浮点数方便阅读
                "symbol": "ETH",
                "block_number": block_number,
                "timestamp": real_time
            }

        elif input_data.startswith('0xa9059cbb'):
            # === 情况 B:  ERC20 转账 ===
            # 需要进一步解码 input_data,检查方法 ID 是否为 transfer (0xa9059cbb)
            
            try:
                # 创建一个临时的合约对象来帮我们要解析，通过交互已有合约的方式
                # tx['to'] 就是被命令的代币合约的地址（比如 USDT 的地址）
                contract = self.w3.eth.contract(address=tx['to'], abi=ERC20_ABI)
                # 解析交易中输入的函数、参数，要求input_data是hex string格式，且必须以0x开头
                func_obj, func_params = contract.decode_function_input(input_data)
                # 获取接收方和金额, 这里的 to 是参数里的接收方，不是合约地址
                # _to、_value在开头ABI中已定义
                receiver = func_params['_to']
                raw_amount = func_params['_value']
                # 与合约交互，获取代币换算精度和符号. .call()用来只读链上状态
                token_symbol = contract.functions.symbol().call()
                token_decimals = contract.functions.decimals().call()

                human_amount = raw_amount / (10 ** token_decimals)

                return {
                    "tx_hash": tx_hash,
                    "type": "ERC20_TRANSFER",
                    "from": tx['from'],
                    "to": receiver,  # 这里的 to 是参数里的接收方，不是合约地址
                    "token_address": tx['to'],      # 合约地址
                    "amount": human_amount,
                    "symbol": token_symbol,
                    "block_number": block_number,
                    "timestamp": real_time
                }
            except ValueError as e:
                return {"type": "DECODE_FAILED",
                         "reason": str(e),
                         "raw_input": input_data
                }
            
        else:
            # === 情况 C:  其他交互 ===
            return {"type": "OTHER_CONTRACT_INTERACTION",
                     "method_id": input_data[:10],
                     "info": "非转账类合约交互",                    
            }    
        
        

if __name__ == "__main__":
    print("正在启动KYT数据采集引擎...")
    # 先实例化一个DatabaseManager数据库管理器对象，建立数据库连接
    db = DatabaseManager(DB_CONFIG)
    db.create_tables()   # 确保数据表结构已经就绪，如果表已经存在，create_tables 方法会自动跳过，不会报错
    # # 再实例化一个 ChainListener 对象，并把 db 对象作为参数塞进去
    listener = ChainListener(db_manager=db)

    test_tx_hash = "0xfc6567db30fd74b27a6d158a0c4852b8faddae02579f529792272633e10ba125"

    print(f"正在解析交易：{test_tx_hash}")

    # 解析交易
    tx_data = listener.decode_transaction(test_tx_hash)

    tx_data['tx_hash'] = test_tx_hash
  
     
    # 判断并入库
    if tx_data.get("type") != "ERROR" and tx_data.get("type") != "DECODE_FAILED":
        print(f"解码成功: {tx_data.get('symbol')} 转账 {tx_data.get('amount')}")

        # 写入数据库
        # 访问 ChainListener 对象的 db 属性（即之前传入的 DatabaseManager 实例），调用它(db)的 insert_transaction 方法，把解析后的交易数据 tx_data 传进去。
        # 写入数据库，并获取返回的成功与否状态
        is_success = listener.db.insert_transaction(tx_data)

        if is_success:            
            # 提交事务（如果是批量处理，这个commit 应该放在循环外面）
            listener.db.commit()
            print("数据已永久写入PostgreSQL 数据库!")
        else:
            print("数据写入失败，已回滚当前事务。")
    else:
        print(f"交易解析失败或跳过，原因：{tx_data}")

    # 关闭数据库连接
    db.close()
    print("测试结束")


    # print(listener.decode_transaction("0x44f4a5cb42c77494e019c0af6ea77f6a7a7f27c88dddab8a8e76a6875a0077f6"))
    # print(listener.decode_transaction("0xfc6567db30fd74b27a6d158a0c4852b8faddae02579f529792272633e10ba125"))
    

