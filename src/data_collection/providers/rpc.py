from web3 import Web3
from typing import List, Dict, Any
from .base import DataProvider
from datetime import datetime

class RPCProvider(DataProvider):
    def __init__(self, rpc_url: str, contract_abi: str):
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        self.contract_abi = contract_abi
        self.simple_check()

    
# 验证节点是否连接成功
    def simple_check(self):        
        if not self.web3.is_connected():
            raise ConnectionError("RPC节点连接失败")
            
        print(f"RPC节点连接成功,当前区块高度为：{self.web3.eth.block_number}")
        return True    
    # 输入input哈希字段，程序自动判断它是ETH“直汇”还是ERC20“合约调用”
    def decode_transaction(self, tx_hash: str) -> dict:
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
        
    def fetch_transactions(self, address: str, start_block: int, end_block: int) -> List[Dict[str, Any]]:
        """
        实现接口要求的方法。
        通过扫描区块日志 (Logs) 或遍历区块 (Blocks) 抓取原始交易，
        调用 self.decode_transaction() 解析，最后返回未标准化的原始字典列表。
        """   
        raw_transactions = []
        #遍历抓取交易逻辑
        return raw_transactions
        