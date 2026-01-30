import pandas as pd
import numpy as np

data = [['Google',10], ['Runoob',12], ['Wiki',13]]

df = pd.DataFrame(data, columns=['Site','Age'])
print(df)


# 2.也可使用字典建立
# df = pd.DataFrame({'site':['Google', 'Runoob', 'Wiki'], 'age':[10, 12, 13]})

# # 使用astype方法设置每列的数据类型
df['Site'] = df['Site'].astype(str)
df['Age'] = df['Age'].astype(float)
print(df)


# 3.使用DataFrame构造函数创建数据帧
ndarray_data = np.array([   # 使用numpy的array创建ndarray.再用DataFrame转换
    ['Google', 10],
    ['Runoob', 12],
    ['Wiki', 13]
])
df = pd.DataFrame(ndarray_data, columns=['Site', 'Age'])
print(df)

# 4.使用字典方法创建数据帧，字典的key作为列名，value作为数据，没有对应的部分数据为 NaN。
data = [{'a': 1, 'b': 2}, {'a': 5, 'b': 10, 'c': 20}]
df = pd.DataFrame(data)
print(df)

import pandas as pd  
data = {
    "calories": [420, 380, 390],
    "duration": [50, 40, 45]
}
df = pd.DataFrame(data)
print(df)
print(df.loc[0])    # 返回第一行
print(df.loc[1])    # 返回第二行
print(df.loc[0, "duration"]) # 返回第0行第二列的值。df.loc[行标签, 列标签]---按标签索引
print(df.iloc[0, 1])   # 返回第一行第二列的值---按位置索引


import pandas as pd  
data = {
    "calories": [420, 380, 390],
    "duration": [50, 40, 45]
}
df = pd.DataFrame(data, index=["day1", "day2", "day3"])
print(df)
print(df.loc["day2"])    # 返回 day2 行
print(df.head(2))   # 返回前两行,如果没有数字2，默认返回前5行



import pandas as pd  # 习惯我们把 pandas 简写为 pd
# 创建Dataframe
data = {
    'Name': ['Tom', 'Jack', 'Steve', 'Ricky'],
    'Age': [28, 34, 29, 42],
    'City': ['Beijing', 'Shanghai', 'Guangzhou', 'Shenzhen']
}
df = pd.DataFrame(data)
print(df)
# 查看前两行数据
print(df.head(2))

# 查看Dataframe的基本信息
print(df.info())

# 查看描述性统计信息
print(df.describe())

# 按年龄排序
df_sorted = df.sort_values(by='Age', ascending=False) # 按Age列降序排序
print(df_sorted)

# 选择指定列
print(df[['Name', 'Age']])  # 选择Name和Age列

# 按索引选择行
print(df.iloc[1:3]) # 选择第2行到第3行(按位置)

# 按照分组统计，按某一列分组进行汇总统计
data = {
    'Name': ['Tom', 'Jack', 'Steve', 'Ricky'],
    'Age': [28, 34, 29, 42],
    'City': ['Beijing', 'Shanghai', 'Guangzhou', 'Shenzhen']
}
df = pd.DataFrame(data)
print(df)

print(df.groupby('City')['Age'].mean()) # 按City列分组. 计算Age列的平均值