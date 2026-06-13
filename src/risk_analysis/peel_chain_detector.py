from collections import defaultdict  # 用来自动分组的数据结构


class PeelchainDetector:
    def __init__(self):
        pass

    def detect(self, trace_tree):        
        # 自动给不存在的 key 一个默认值（这里是空列表 list）,defaulltdict帮忙把逻辑自动化了
        grouped_txs = defaultdict(list)     # 创建一个空的字典grouped_txs，用来存储可疑地址和它们对应的金额列表
        risk_reports = []    # 创建空列表，放专门的剥皮发送地址.收到地址后把大部分金额再转给下一个地址
        score = 0

        # 2.遍历追踪模块（trace_engine.py）得出的数据trace_tree
        for tx in trace_tree:                   
            
            
            # 把这一笔金额，追加放入这个发送方地址对应的列表中,每一轮循环都会被更新
            grouped_txs[tx['from']].append({
                'amount': tx['amount'], 
                 'to': tx['to'], 
                 'current_depth': tx['current_depth']                
            })            
                   
    
        # 3.逐个对发送地址进行分析
            # 1.如果存在多个金额相同的情况，就说明这个地址可能在进行peelchain操作
            # 3.对每个发送地址的金额列表进行分析，统计
            # 4.如果发现某个地址的金额列表中存在多个金额相同的情况，就把这个地址和它对应的金额列表记录下来，作为可疑地址
            # 5.最后把所有的可疑地址和它们对应的金额列表返回，供后续的审计和调查使用  

            # tx_records在for 循环在运行时“自动创建并赋值”的变量，是一个列表
        for sender, tx_records in grouped_txs.items():
            
            
            # 一个地址可以有多次发出转账行为，所以tx_records其实代表了交易记录列表。如果只转出了一笔钱，就不可能是剥皮链了，直接跳过
            if len(tx_records) < 2:
                continue
            
            # 从列表中拿字典，分装给每个循环变量字典record中，需要用列表推导式，才能把每个字典对应的amount值拿出来放到新的列表amounts中
            amounts = [record['amount'] for record in tx_records]

            total_amount = sum(amounts)
            max_amount = max(amounts)          

            # 规则1：自动化打散
            # set()函数可以把一个列表转换成一个集合，集合中的元素是唯一的，可以自动去重。
            if len(set(amounts)) == 1 and len(amounts) > 2:
                report = {
                    "sender": sender,
                    "amounts": amounts,
                    "score": 90,
                    "label": "Automated Fan-out Detected",
                } 
                risk_reports.append(report)                
                # 如果判定为打散，通常不会再作为剥皮链起点，直接检查下一个人
                continue

            # 规则2：金额悬殊,深度剥皮链的特点是第一笔转出金额远大于后续转出金额，如果第一笔转出金额占总转出金额的比例超过80%，就有可能是剥皮链的起点
            if max_amount > 0.8 * total_amount: 
                current_suspect = sender
                path_amounts = []   # 创建一个空列表，用来存储剥皮链路径上的主资金金额，后续会用来分析金额递减的特征
                
                while current_suspect in grouped_txs:
                    records = grouped_txs[current_suspect]
                    current_max = 0
                    next_suspect = ""      # 创建一个空的字符串变量，用来存储下一个可疑地址                    

                    for r in records:
                        
                        if r['amount'] > current_max:
                            current_max = r['amount']
                            next_suspect = r['to']
                    path_amounts.append(current_max)  

                    if next_suspect == current_suspect:
                                break
                    current_suspect = next_suspect                  

                    if len(path_amounts) >= 3:
                        # 特征1：判断主力资金是否持续递减
                                                
                        list1 = [
                            path_amounts[i] > path_amounts[i+1] 
                            for i in range(len(path_amounts)-1)
                        ]
                        decreasing = all(list1)    
                                                   
                        
                        # 特征2：计算每次剥离的金额（差值）
                        diffs = [
                            path_amounts[i] - path_amounts[i+1]  
                            for i in range(len(path_amounts)-1)
                        ]
                        # 特征3：小额剥离判定
                        small_peel = max(diffs) < 0.1 * path_amounts[0]

                        
                        # 终极审判：必须同时满足递减和稳定剥离
                        if decreasing and small_peel:
                        
                            risk_reports.append({
                                "sender": sender,
                                "amounts": path_amounts.copy(),     # 记录完整的犯罪资金轨迹
                                "score": 100,                       # 致命级风险，直接阻断
                                "label": "Dynamic Peel Chain Detected",
                                "to_suspect": next_suspect
                            })             
            
                
        # 提交报告
        return risk_reports

       
