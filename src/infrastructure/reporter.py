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
    
    def get_simple_html_report(self, df):
        # justify='center' 让内容居中
        # classes 允许我们后续通过 CSS 给名称为为risk_table的表格加样式,让表格更好看
        return df.to_html(index=False, justify='center', classes='risk_table')

    # 新增方法：生成(内嵌CSS）HTML 格式的报告
    def get_styled_html_report(self, df): 

        # 1.定义高亮函数，如果风险等级是 Critical，整行变红
        # axis=1：按行处理。故row代表DataFrame中的每一行数据，pandas会自动传入
        def highlight_critical(row):   
            # 这里的样式：浅红色背景 + 深红色加粗文字
            critical_style = 'background-color: #ffe6e6; color: #b30000; font-weight: bold;'
            if row['risk_level'] == 'Critical':
                return [critical_style] * len(row)  # 整行的每一列都应用这个样式
            return [''] * len(row)  # 如果不是 'Critical'，就返回空字符串列表

        # 2.应用样式并格式化
        # df.style ，添加DataFrame的样式。.apply()应用到某个函数.format()控制数字的样式
        style_df = df.style.apply(highlight_critical, axis=1).format({
            'eth_value': 'U{:.2f}',     # {}为数据占位符。金额前加U，保留2位小数
            'total_risk_score': '{:.0f} pts'    # .0f 保留0位小数（即取整）。pts为单位
        })

        # 3.转化为带样式（内嵌CSS）的 HTML
        #注意：Styler 的 to_html 会包含 CSS 代码，确保邮件客户端能识别
        return style_df.to_html()
        
        
