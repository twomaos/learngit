# -*- coding: utf-8 -*-
"""
Created on Sat Apr 14 22:43:17 2017

@author: twomaos

Ver1.1

功能：查询并打印组员的打卡信息，包括单词数与学习时间是否满足划水判定条件。

Update：
1.可自由设定查卡日期（10天内）
2.可应付目前遇到的各种情况，包括时光机打卡的影响
3.打印格式优化：标题栏自动化/附注查询时间

后续改进方向：
1.导出图片
2.发送到微信
3.召唤未打卡的组员
"""


import requests
from bs4 import BeautifulSoup
import re
import time
from prettytable import PrettyTable

#获取当地时间，用于确定默认查卡时间
def getTime():
    t = time.localtime(time.time())
#中午12点前查的是前一天的卡，五点后查当天的卡
    if t.tm_hour < 12:
        day = t.tm_mday - 1
    else:
        day = t.tm_mday
#此处返回的是一个int类型
    return day
        
def getCookie(cookies):
#cookie来自网页工具
    raw_cookies = '__utma=183787513.127891850.1492176187.1492355472.1492358952.8;__utmb=183787513.1.10.1492358952;__utmc=183787513;__utmt=1;__utmz=183787513.1492176187.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none);_ga=GA1.2.127891850.1492176187;auth_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6InR3b21hb3MiLCJkZXZpY2UiOjAsImlzX3N0YWZmIjpmYWxzZSwiaWQiOjEyNDMwOTMwLCJleHAiOjE0OTMyMjI5NTJ9.jsQqAPKGlex_hQMIf5ZTEfey5_IPX0HrHzI6hVshlpI;csrftoken=aIslKKfjsSL0PXwRTD8OuTsGmtJ6aVXX;sessionid=".eJyrVopPLC3JiC8tTi2KT0pMzk7NS1GyUkrOz83Nz9MDS0FFi_VccxMzc3zy0zPznKAKdZB1ZwI1GhqZGBtYGhvUAgC33h9m:1cz1DB:mme1G-d1L_ISpdJdXZdX75DzCSU";language_code=zh-CN;userid=12430930;'
    for line in raw_cookies.split(';')[:-1]:
        key,value=line.split('=',1)
        cookies[key]=value
      
def memberLinks(links):
#用cookie登陆并读取组员名单
    for n in range(2):
        url = 'https://www.shanbay.com/team/members/?page=' + str(n+1)
        r = requests.get(url,cookies = cookies)
        html = r.text
        soup = BeautifulSoup(html,'html.parser')
#将组员个人页面的链接存入links列表中
        for link in soup('a','nickname'):
            links.append(link.attrs['href'])

#进入组员个人页面并提取信息，num为组员序号，checkday为查卡日期
def getMemberInfo(num, checkday=getTime()):
#进入组员的个人打卡页并解析
    raw_url = 'https://www.shanbay.com'
    member_link = raw_url + links[num]
    r = requests.get(member_link,cookies = cookies)
    html = r.text
    soup = BeautifulSoup(html,'html.parser')
    username = soup('span','username')[0].a.string
    
#匹配checkday信息，检查组员在checkday是否打卡
    dates = soup('div','span4')
    pattern_date = re.compile(str(checkday))
    checkQ = False
    for date in dates[:-1]:
        match = pattern_date.search(date.string.replace('\n','').replace(' ','').split(',')[0])
        if match:
            checkQ = True
            notes = date.parent.parent.parent.parent('div','note')[0]
            break


#组员打卡信息爬取
#初始化
    wordQ = False
    timeQ = False    
#先判断组员是否打卡，如果打卡了则判断单词数与分钟数是否满足条件
    if checkQ:        
#以下正则表达式用于提取组员打卡的单词数与分钟数，注意note是个列表
        pattern_note = re.compile(r'\d+个单词|\d+分钟')
        note = pattern_note.findall(notes.string.replace('\n','').replace(' ',''))
#如果没有读取到单词数，则temp列表长度为1，单词数word=0
        if len(note) == 1:
            word = 0
            wordQ = False            
#判定单词数是否达标，单词数须大于100个
        elif eval(re.match(r'\d+',note[0]).group(0)) >= 100:
            wordQ = True
            word = eval(re.match(r'\d+',note[0]).group(0))
        else:
            wordQ = False
            word = eval(re.match(r'\d+',note[0]).group(0))
#判定时间是否达标，时间须大于10分钟
        if eval(re.match(r'\d+',note[-1]).group(0)) >= 10:
            timeQ = True
        time = eval(re.match(r'\d+',note[-1]).group(0))
        if wordQ and timeQ:
            result = '成功'
        elif not wordQ:
            result = '失败，单词数不够'
        else:
            result = '失败，学习时间不够'
#将判定结果存入字典，未改变的值为False
        check[username] = [word, wordQ, time, timeQ, result]        
#如果没有打卡，则字典存入“未打卡”
    else:
        check[username] = ['-', '-','-','-','未打卡']

def checkOutput(check):
    print('\n\n{:^50}'.format('4月'+str(checkday)+'日' +'【麻花麻花】打卡情况统计') )
    pt = PrettyTable(["小组成员","打卡","单词数(个)","学习时间(分钟)"])
    pt.align["小组成员"] = "l"# Left align city names
    pt.padding_width = 1# One space between column edges and contents (default)
    for key in check:
        pt.add_row([str(key), str(check[key][4]), str(check[key][0]), str(check[key][2])])
    print(pt)
#格式化输出查询时间
    print('{:>60}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) ))

def main():
    getCookie(cookies)
    memberLinks(links)
    for i in range(len(links)):
        getMemberInfo(i, checkday)
    checkOutput(check)
    
checkday = getTime()
cookies = {}
links = []
check = {}
main()


