import requests

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

    def send_telegram_photo(self, caption, image_path):
        url = self.base_url + "/sendPhoto"
        with open(image_path, 'rb') as img_file:
            files = {'photo': img_file}
            data = {'chat_id': self.chat_id, 'caption': caption}
            requests.post(url, data=data, files=files)
            print("图片汇总已推送到 Telegram")

