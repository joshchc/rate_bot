from datetime import datetime, date, timedelta
import json
import requests
import os
import re


class Rate:

    def get_response(self):

        url = 'https://www.xe.com/api/protected/midmarket-converter/'

        headers = {
            'authorization':'Basic bG9kZXN0YXI6cHVnc25heA==',
            'coockie':'_gcl_au=1.1.808921550.1734055440; amp_470887=vOY0hx7Bi7UQD8s1Js3xXA...1ieus4c7e.1ieus4c7k.1.1.2; _ga=GA1.1.1364532436.1734055441; IR_gbd=xe.com; IR_12610=1734055440637%7C0%7C1734055440637%7C%7C; _fbp=fb.1.1734055440926.468066597229088599; _uetsid=854b14e0b8f611ef8949057be1b86021; _uetvid=854b6000b8f611efba3871caf8a264cf; _y2=1%3AeyJjIjp7fX0%3D%3AMTc0OTg2MjMwNA%3D%3D%3A2; __hs_cookie_cat_pref=1:true_2:true_3:true; __hstc=123240596.812a0e88af79c89b4ddf637658f2cd2c.1734055442985.1734055442985.1734055442985.1; hubspotutk=812a0e88af79c89b4ddf637658f2cd2c; __hssrc=1; __hssc=123240596.1.1734055442985; __gads=ID=9407836568f59aae:T=1734055442:RT=1734055442:S=ALNI_MaPqZd9ldf1HQBQj5X5K06w0i-8-A; __gpi=UID=00000f8d5acf361a:T=1734055442:RT=1734055442:S=ALNI_Mb66OvEZJ5BnrovjFcl_-1taOf9Nw; __eoi=ID=fc6ab2cd99d4a63e:T=1734055442:RT=1734055442:S=AA-AfjayYSqrVH_s90nPRYQ3jBMS; _yi=1%3AeyJsaSI6bnVsbCwic2UiOnsiYyI6MSwiZWMiOjksImxhIjoxNzM0MDU1NDYyMTM0LCJwIjoxLCJzYyI6MjF9LCJ1Ijp7ImlkIjoiNzc1NGFhNzAtOTYxMC00ZjU4LWExZTYtNmQyMzQ3OTVjYmEzIiwiZmwiOiIwIn19%3ALTE0MzE4NDYxMTI%3D%3A2',
            'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }

        return requests.get(url, headers=headers).text
    
    def rate_json(self):
        data = json.loads(self.get_response())
        self.rate_time = datetime.fromtimestamp(data['timestamp']/1000)
        self.data = data['rates']
        
    def main(self, curr: str):
        try:
            self.rate_json()
            self.data = self.data[f'{curr.upper()}']

            return  f"""USD -> {curr.upper()}: {self.data:.6f}\n{curr.upper()} -> USD: {(1.0/self.data):.6f}"""
        except KeyError:
            return "查詢錯誤"
        
    def currency_conversion(self, text: str):
        try:
            self.rate_json()
            s1 = text[:3]
            s2 = text[-3:]
            c1 = self.data[f'{s1.upper()}']
            c2 = self.data[f'{s2.upper()}']

            return f"""{s1.upper()} -> {s2.upper()}: {(c2/c1):.6f}\n{s2.upper()} -> {s1.upper()}: {(c1/c2):.6f}"""

        except KeyError:
            return "查詢錯誤"

    def compare_currency(self, text:str):
        self.rate_json()
        s1 = text[:3]
        s2 = text[-3:]
        c1 = self.data[f'{s1.upper()}']
        c2 = self.data[f'{s2.upper()}']
        return c2/c1