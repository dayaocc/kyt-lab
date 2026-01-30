import pandas as pd  # 习惯我们把 pandas 简写为 pd
series = pd.Series([1, 2, 3, 4], name='A') # 创建一个名为 A 的 Series,默认索引
print(series)

custom_index = [1, 2, 3, 4] # 自定义索引
series_with_index = pd.Series([1, 2, 3, 4], index=custom_index, name='B')
print(series_with_index)

import pandas as pd
a = [1, 2, 3]
myvar = pd.Series(a)
print(myvar)  # 输出整个 Series
print(myvar[1]) # 输出 2，索引从 0 开始

import pandas as pd
a = ["Google", "Runoob", "Wiki"]
myvar = pd.Series(a, index = ["x", "y", "z"])
print(myvar)  
print(myvar["y"]) # 输出 Runoob

import pandas as pd
sites = {1: "Google", 2: "Runoob", 3: "Wiki"}   # key:value 是 字典 dict 的语法，只能用 {}
myvar = pd.Series(sites)
print(myvar)
print(myvar[3]) # 输出 Wiki

import pandas as pd
sites = {1: "Google", 2: "Runoob", 3: "Wiki"}
myvar = pd.Series(sites, index = [1, 2], name="RUNOOB-Series-TEST") # 通过 index 参数指定索引
print(myvar)

data = [1, 2, 3, 4, 5, 6]
index = ["a", "b", "c", "d", "e", "f"]
s = pd.Series(data, index=index)
print(s)

print("索引:", s.index)
print("数据：", s.values)
print("数据类型：", s.dtype)
print("前两行数据：", s.head(2))

s_doubled = s.map(lambda x: x * 2)  # 将指定函数应用于 Series 中的每个元素
# lambda x: x * 2 等价于 def func(x): return x * 2
print("每个元素乘以2后的结果:\n", s_doubled)

cumsum_s = s.cumsum()   # 计算累计和
print("累计和:\n", cumsum_s)

print("缺失值判断:\n", s.isnull()) # 判断缺失值，返回布尔值 Series

sorted_s = s.sort_values()   # 对 Series 中的元素进行排序（按值排序）
print("排序后的 Series:\n", sorted_s)