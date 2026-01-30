import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import os
import datetime

# 为了不让程序崩溃，我们需要给图表设置一个固定的保存路径。
class RiskReporter:
    def __init__(self, output_dir="outputs"):
        self.output_dir = output_dir    # 指定输出目录
        # 如果 outputs 文件夹不存在，自动创建一个
        if not os.path.exists(self.output_dir):  # os.path.exists()检查路径是否存在的函数
            os.makedirs(self.output_dir)  # 创建目录
        # 设置绘图风格
        sns.set_theme(style="whitegrid")
        
    def create_dataframe(self, raw_data, columns):
        # 把元组列表转化成 Pandas 表格
        column_names = ['tx_hash', 'eth_value', 'sender']
        return pd.DataFrame(raw_data, columns=column_names)

    def draw_risk_chart(self, df):
        # 绘图逻辑
        plt.figure(figsize=(10, 6))  # 设置画布大小
        # 按发送者汇总金额
        # seaborn绘制柱状图的核心函数---barplot
        chart = sns.barplot(
            data=df, 
            x='sender', 
            y='eth_value', 
            palette='magma'   # 选择一个专业的配色方案:连续型渐变色系
        )
        # 3. 添加标题和标签，让图表能“自解释”     
        today = datetime.date.today()
        plt.title(f"今日高危交易汇总{today}", fontsize=14)
        plt.ylabel("涉及总金额(ETH)", fontsize=12)
        plt.xlabel("发送者地址", fontsize=12)
        # 固定文件名，实现“覆盖旧图”
        chart_path = os.path.join(self.output_dir, "latest_risk_summary_chart.png")
        plt.savefig(chart_path)  # 保存图表到指定路径
        plt.close()  # 关闭图表，释放内存
        return chart_path

    def save_excel(self, df, filename):
        # 导出为 Excel 审计底稿
        path = os.path.join(self.output_dir, filename)
        df.to_excel(path, index=False)
        return path