blacklist = ["0x456", "0x999"]

# 一种写法：像人类一样说话。
# 我们直接判断这笔交易的 hash 是否在黑名单这个“圈子”里
if tx["hash"] in blacklist:
    print(f"⚠️ 警报！发现黑名单交易：{tx['hash']}")
    
# 另一种写法：for 会自动把 blacklist 里的每个地址赋值给 address
for address in blacklist:
    if tx["hash"] == address:
        print(f"🎯 命中黑名单地址：{address}")
        # 找到了就停下，不用再检查剩下的地址了，这叫“跳出循环”
        break

# 定义函数checkValue
def checkValue(value, datalist):
    if (value in datalist):
        return True
    return False


blacklist = ["0x456", "0x999"]

# 像人类说话一样，一次性检测完毕
if tx["hash"] in blacklist:
    print(f"发现黑名单交易:{tx['hash']}")

# 利用for循环逐一检查
for address in blacklist:   # address是临时变量名
    if tx["hash"] == address:
        print(f"发现黑名单交易:{tx['hash']}")
        break

# 假设这是一笔新交易
tx = {
    "from": "0x123",
    "to": "0x456",
    "value": 2.0
}
# 逻辑判断：发送方 OR 接收方 在黑名单里吗？
if tx["from"] in blacklist or tx["to"] in blacklist:
    print("警告：发现与黑名单相关的资金流动")

# 引入else进行处理分支
if tx["from"] in blacklist or tx["to"] in blacklist:
    risk_level = "High"
elif tx["value"] > 100:
    risk_level = "Medium(Manual audit)"
else:
    risk_level = "low"
# f-string是字符串语法，字符串里直接写变量/表达式，用 {...} 把它们“嵌进去”，运行时会自动替换成对应的值。
print(f"这笔交易的风险评级为：{risk_level}")


# 顶级风险逻辑：既是黑名单，又是大额
if (tx["from"] in blacklist) and (tx["value"] > 100):
    risk_level = "Critical"
print("发现顶级风险！需要立即冻结并生成Case Report！")

#将上述逻辑用函数表示出来，方便重复使用该逻辑
blacklist = ["0x456", "0x999"]
tx = {
    "from": "0x123",
    "to": "0x456",
    "value": 2.0
}
# 在 Python 中，return 的作用是“把结果扔出机器”。它后面直接跟你要返回的值，不能写赋值语句。
def analyze_risk(tx_data):
    if tx_data["from"] in blacklist or tx["to"] in blacklist:
        return "High"
    elif tx_data["value"] > 100:
        return "Medium(Manual audit)"
    else:
        return "low"
# 运行函数并将从变量作用域中“扔出来”的结果存入变量 result.
result = analyze_risk(tx)
print(f"这笔交易的风险评级为：{result}")


'''
def hello_function(greeting):
    return '{} Function.'.format(greeting) 
# {}是一个占位符，真正把 'Hi' 填进去的是后面的 .format(greeting)。把 greeting 填到 {} 的位置
# .format(...) 是 字符串的格式化方法 效果等同于 f-string
print(hello_function('Hi'))

# 同样输出效果的f-string写法
def hello_function(greeting):
    return f"{greeting} Function."
print(hello_function("Hi"))

# 函数里也可以传递多个参数
def hello_function(greeting, name='you'):
    return '{}, {}'.format(greeting, name) 
print(hello_function('Hi'))

def hello_function(greeting, name='you'):
    return '{}, {}'.format(greeting, name) 
print(hello_function('Hi', name = 'chaolyn'))
'''


# 可变参数
# *args：把“多出来的位置参数”收集成一个 tuple（元组）。**kwargs：把“多出来的关键字参数”收集成一个 dict（字典）
def student_info(*args, **kwargs):
    print(args)  
    print(kwargs)  
    # print(type(args))   # 元组
    # print(type(kwargs))  # 字典
student_info('math', 'Art', name='John', age=22)

#或者在外部直接调用
courses = ['Math','Art']
info = {'name': 'John','age': 22}
student_info(*courses, **info)

# 每个月天数列表
month_days = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
def is_leap(year):
    '''返回True就是闰年，返回False 就是平年 '''
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
def days_in_month(year, month):
    #返回对应年份，月份的天数
    if not 1 <= month <= 12:
        return 'invalid month'
    if month == 2 and is_leap(year):
        return 29
    return month_days[month]
print(days_in_month(2017, 2)) 

