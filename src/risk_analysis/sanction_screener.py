import time
import requests

class SanctionScreener:
    def __init__(self, api_key=None, use_mock=True):    #use_mock默认为True，使用本地假定的黑名单
        self.api_key = api_key
        self.use_mock = use_mock
        self.api_url = "https://api.opensanctions.org/v1/search"    # 设置API的URL地址

        # 本地模拟的 OFAC（美国财政部外国资产控制办公室）SDN 黑名单
        self.mock_blacklist = {
            "0x黑客首脑": {
                "entity": "Lazarus Group(朝鲜黑客组织)",
                "sanction_date": "2019-09-13"              
            },
            "0x被制裁的混币器": {
                "entity": "Tornado Cash(混币器)",
                "sanction_date": "2022-08-08"
            }
        }

    def check_address(self, address):
        """
        检查给定的地址是否在制裁名单中。
        返回: 命中则返回风险报告(dict)，安全则返回 None
        """
        if self.use_mock:
            return self._mock_api_call(address)
        
        else:
            return self._real_api_call(address)
    
    def _mock_api_call(self, address):
        """
        模拟API调用，检查地址是否在本地黑名单中。
        """
        time.sleep(0.1)  # 模拟网络请求延迟，真实感受API的耗时
        if address in self.mock_blacklist:
            info = self.mock_blacklist[address]     #address是字典的键，这里是要被检查的参数
            return {
                "sender": address,
                "score": 100,   # 涉敏制裁，无条件 100 分一票否决
                "label": "OFAC Sanctioned Entity",
                "details": info
            }
        return None
    
    def _real_api_call(self, address):
        """
        预留的真实API调用方法，使用OpenSanctions API检查地址是否在制裁名单中。
        """
        try:
            # 这里是真实的请求逻辑示例
            headers = {"Authorization": f"ApiKey {self.api_key}"}
            params = {"q": address, "schema": "CryptoWallet"}

            response = requests.get(self.api_url, headers=headers, params=params, timeout=3)
            # xxx.get("xxx")表示安全地获取字典中键为"xxx"的值，如果键不存在则返回None，避免KeyError异常
            if response.status_code == 200 and response.json().get('results'):
                return {
                    "sender": address,
                    "score": 100,
                    "label": "OFAC Sanctioned Entity(live API)",
                    "details": response.json()['results'][0]  # 假设返回的结果中包含制裁实体的详细信息
                }
        except requests.exceptions.RequestException as e:
            print(f"[SanctionScreener] API 调用失败：{e}")
        
        return None







