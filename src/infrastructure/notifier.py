import requests
import smtplib  #发送邮件的标准库模块
from email.mime.text import MIMIText    # 用于构造邮件正文
from email.mime.multipart import MIMEMultipart  # 用于构造带附件的邮件

class TelegramBot:
    def __init__(self, token, chat_id): 
        # token 和 chat_id 小写表示局部参数，存放在对象属性里，方便后续方法调用
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def send_telegram_msg(self, text):
        url = f"{self.base_url}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": text}
        requests.post(url, data=payload)        #目标地址, 请求数据

    def send_telegram_photo(self, caption, image_path):   # caption 图片说明文字, image_path 图片文件路径
        url = self.base_url + "/sendPhoto"
        with open(image_path, 'rb') as img_file:
            files = {'photo': img_file}
            data = {'chat_id': self.chat_id, 'caption': caption}
            requests.post(url, data=data, files=files)
            print("图片汇总已推送到 Telegram")

class EmailNotifier:
    def __init__(self, smtp_config):
        # 从配置中读取服务器地址、端口、发件人账号和授权码
        self.server = smtp_config['server']
        self.port = smtp_config['port']
        self.user = smtp_config['user']
        self.password = smtp_config['password']
    def send_html_report(self, receiver, subject, html_content, attachment_path=None):    # receiver 收件人地址, subject 邮件主题, content 邮件正文, attachment_path 附件文件路径
        # 1.准备邮件容器
        msg = MIMEMultipart()
        msg['From'] = self.user     # 设置邮件头-发件人
        msg['To'] = receiver    # 设置邮件头-收件人
        msg['Subject'] = subject    # 设置邮件头-主题
        # 2.添加邮件正文
        msg.attach(MIMIText(html_content, 'html'))  # 邮件协议要求每一块内容必须声明类型，plain表示纯文本。一般转换为html更好看
        # 3.添加附件（如果有）
        # if attachment_path:
        #     with open(attachment_path, 'rb') as f:
        #         part = MIMEMultipart(f.read())
        #         part.add_header()
        # pass # 占位符，代码逻辑未完成。保证程序能跑通
        with smtplib.SMTP_SSL(self.server, self.port) as smtp:
            smtp.login(self.user, self.password)
            smtp.send_message(msg)
