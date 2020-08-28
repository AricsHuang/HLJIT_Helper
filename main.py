# -*- coding: UTF-8 -*-
# @Time     : 2020/5/23 下午11:27
# @Author   : Arics
# @Email    : 739386753@qq.com
# @File     : main.py
# @Software : PyCharm
# @IDE      : PyCharm

import requests
from bs4 import BeautifulSoup
from PIL import Image
import base64
import re
import time
import urllib
import datetime
import calMaker


###########
## config
###########
'''
更改你的用户名和密码，并且输入第一周的星期一的日期
百度云 网络图片文字识别API 请自行到官网申请
'''
username = "[学号]"
password = "[密码]"
BaiduAPI_client_id = "[client_id]"
BaiduAPI_client_secret = "[client_secret]"
'''
第一周周一的日期
'''
fyear = 2020
fmonth = 8
fday = 17


###########
## params
###########
'''
默认设置，无需改动
'''
headers = {
    'Connection': 'keep-alive',
    'Host': 'jw.hljit.edu.cn',
    'Referer': 'http://jw.hljit.edu.cn',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36',
}
data = {
    "__VIEWSTATE": "dDwyODE2NTM0OTg7Oz5N%2BXuKJszfD%2BydWydHqh9DqM8uHg%3D%3D",
    "txtUserName": username,
    "TextBox2": password,
    "txtSecretCode": "",
    "RadioButtonList1": "%D1%A7%C9%FA",
    "Button1": "",
    "lbLanguage": "",
    "hidPdrs": "",
}
homeUrl = "http://jw.hljit.edu.cn/default2.aspx"
checkCodeUrl = "http://jw.hljit.edu.cn/CheckCode.aspx"

weekDic = {'一': 'MO', '二': 'TU', '三': 'WE', '四': 'TH', '五': 'FR', '六': 'SA', '日': 'SU'}
weekNumDic = {'MO': 0, 'TU': 1, 'WE': 2, 'TH': 3, 'FR': 4, 'SA': 5, 'SU': 6}
sectionStartTimeDic = {'1': datetime.timedelta(hours=8), '2': datetime.timedelta(hours=9), '3': datetime.timedelta(hours=10, minutes=10), '4': datetime.timedelta(hours=11, minutes=10), '5': datetime.timedelta(hours=13, minutes=30),
                       '6': datetime.timedelta(hours=14, minutes=30), '7': datetime.timedelta(hours=15, minutes=30), '8': datetime.timedelta(hours=16, minutes=30), '9': datetime.timedelta(hours=18), '10': datetime.timedelta(hours=19, minutes=10)}
sectionEndTimeDic = {'1': datetime.timedelta(hours=8, minutes=50), '2': datetime.timedelta(hours=9, minutes=50), '3': datetime.timedelta(hours=11), '4': datetime.timedelta(hours=12), '5': datetime.timedelta(hours=14, minutes=20),
                     '6': datetime.timedelta(hours=15, minutes=20), '7': datetime.timedelta(hours=16, minutes=20), '8': datetime.timedelta(hours=17, minutes=20), '9': datetime.timedelta(hours=18, minutes=50), '10': datetime.timedelta(hours=20)}
firstWeekMonday = datetime.datetime(fyear, fmonth, fday)

def getHTML(url, data, headers):
    '''简单的获取网页的html'''
    response = requests.get(url=url, headers=headers, params=data)
    response.encoding = response.apparent_encoding
    return response

def getHiddenValueAndToken():
    '''获取教务网站 __VIEWSTATE 和 用户会话token'''
    response = getHTML(url=homeUrl, data=None, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    info = soup.find(name="input", attrs={'name': '__VIEWSTATE'})
    if info:
        hiddenValue = info.get('value')
        token = response.url.split("(")[1].split(")")[0]
    else:
        hiddenValue = None
        token = None

    return {"hidenValue": hiddenValue, "token": token}

def getVeriCode(checkCodeUrl):
    '''通过百度云 网络图片文字识别API 识别验证码'''
    def getToken():
        '''这是获取百度云api的 token'''
        # client_id 为官网获取的AK， client_secret 为官网获取的SK
        host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=' + BaiduAPI_client_id + '&client_secret=' + BaiduAPI_client_secret
        response = requests.get(host)
        if response:
            return response.json()

    # 通过重复请求寻找到可以识别的验证码
    while(True):
        response = requests.get(url=checkCodeUrl)
        with open("YanZhengMaPic/yanzheng.gif", "wb") as f:
            f.write(response.content)
        # 网站的验证码图片为 gif 格式，需要转换成百度API可以接受的格式，以下转换为了 jpeg
        Image.open("YanZhengMaPic/yanzheng.gif").convert("RGB").save("YanZhengMaPic/yanzheng.jpeg")

        API_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/webimage"
        # 二进制方式打开图片文件
        f = open('YanZhengMaPic/yanzheng.jpeg', 'rb')
        img = base64.b64encode(f.read())

        params = {"image": img}
        access_token = getToken()['access_token']
        API_url = API_url + "?access_token=" + access_token
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        response = requests.post(API_url, data=params, headers=headers)
        if response:
            if response.json()["words_result"]:
                veriCodeText = response.json()["words_result"][0]["words"]
                # 去除特殊字符
                veriCodeText = re.sub(u"([^\u4e00-\u9fa5\u0030-\u0039\u0041-\u005a\u0061-\u007a])", "", veriCodeText)
                # 判断验证码长度
                if len(veriCodeText) == 4:
                    break
    return veriCodeText

def getCurriculum(personName, token):
    '''
    获取学生个人课表
    '''
    tmpName = personName.encode('gbk')
    tmpName = urllib.parse.quote(tmpName)

    data = {
        'xh': username,
        'xm': tmpName,
        'gnmkdm': 'N121603',
    }

    url = "http://jw.hljit.edu.cn/(" + token + ")/xskbcx.aspx"

    r = requests.get(url=url, params=data, headers=headers)
    r.encoding = r.apparent_encoding

    soup = BeautifulSoup(r.text, 'html.parser')
    curriculum = soup.find(name='table', attrs={'id':'Table1'})
    return curriculum

def getIcs(curriculum, calName):
    '''
    保存 .ics 文件
    '''
    def makeTimeDic(timeinfo):
        week = weekDic[timeinfo[1]]
        timeinfo = timeinfo[3:]
        timeinfo = timeinfo.split('节{第')
        section = timeinfo[0].split(',')
        rou = timeinfo[1].replace('周}', '').split('-')
        return {'week': week, 'section': section, 'round': rou}
    curriculum = str(curriculum).replace("<br/>", "\n")
    soup = BeautifulSoup(curriculum, 'html.parser')
    calendar = calMaker.Calendar(calendar_name=calName)

    tds = soup.find_all(name="td")
    for td in tds:
        infos = td.text
        infoList = infos.split("\n\n")

        for each in infoList:
            if len(each) > 10:
                tmpList = each.split("\n")
                className = tmpList[0]
                kind = tmpList[1]
                timeinfo = makeTimeDic(tmpList[2])
                teacher = tmpList[3]
                addr = tmpList[4]

                calMaker.add_event(calendar,
                          SUMMARY=className,
                          DTSTART=firstWeekMonday + datetime.timedelta(days=(int(timeinfo['round'][0])-1)*7+weekNumDic[timeinfo['week']]) + sectionStartTimeDic[timeinfo['section'][0]],
                          DTEND=firstWeekMonday + datetime.timedelta(days=(int(timeinfo['round'][0])-1)*7+weekNumDic[timeinfo['week']]) + sectionEndTimeDic[timeinfo['section'][1]],
                          DESCRIPTION="类型：" + kind + r"\n老师：" + teacher,
                          LOCATION=addr,
                          COUNT=int(timeinfo['round'][1])-int(timeinfo['round'][0]),
                          BYDAY=timeinfo['week'],)
    # print(calendar.get_ics_text())
    calendar.save_as_ics_file()

def getPEClass():
    '''
    选定体育选修科
    '''
    tmpName = personName.encode('gbk')
    tmpName = urllib.parse.quote(tmpName)
    data = {
        'xh': username,
        'xm': tmpName,
        'gnmkdm': 'N121102',
    }

    url = "http://jw.hljit.edu.cn/(" + token + ")/xstyk.aspx"

    r = requests.get(url=url, params=data, headers=headers)
    r.encoding = r.apparent_encoding

    soup = BeautifulSoup(r.text, 'html.parser')
    ListBox1 = soup.find(name="select", attrs={'id': 'ListBox1'})
    print(ListBox1)

def loginOut(token, username, hiddenValue):
    '''
    用户登出函数
    '''
    # dDwxMjg4MjkxNjE4Ozs+XqTrohS45CVc3Yq3WpJlitKUEtw=
    url = "http://jw.hljit.edu.cn/(" + token + ")/xs_main.aspx?xh="+username
    data = {
        "__EVENTTARGET": "likTc",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": "dDwxMjg4MjkxNjE4Ozs+XqTrohS45CVc3Yq3WpJlitKUEtw=",
    }
    response = requests.post(url=url, data=data, headers=headers)
    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, 'html.parser')
    login_box = soup.find(name='div', attrs={'class':'login_main'})
    if login_box:
        aCommandUI.formatPrint("登出成功")
    else:
        aCommandUI.formatPrint("登出失败，请服装以下链接到浏览器登出")
        print("---- " + url)

def judgeTempFlag(tempFlag):
    '''判断哨兵状态'''
    return tempFlag.lower() == 'y' or tempFlag.lower() == 'yes'

class CommandUI():
    '''命令行UI界面'''
    def welcome(self):
        with open("./welcome_message.dat", "r") as f:
            welcomeMsg = f.read()
        print(welcomeMsg)

    def formatPrint(self, message, level="INFO"):
        '''
        level: DEBUG、INFO、WARNING、ERROR、CRITICAL
        '''
        time = datetime.datetime.now().strftime('%X')
        print("[{}] {} {}".format(level, time, message))

    def getLoginInfoFail(self, hiddenValue, veriCode, token):
        self.formatPrint("信息获取不完全，请重试或检查相关函数")
        print("----hiddenValue: " + hiddenValue)
        print("----veriCode: " + veriCode)
        print("----token: " + token)

    def loginFail(self, HTMLText):
        if "用户名不存在或未按照要求参加教学活动" in HTMLText:
            self.formatPrint("用户名不存在或未按照要求参加教学活动！！", level="WARNING")
        elif "密码错误" in HTMLText:
            self.formatPrint("密码错误！！", level="WARNING")
        elif "验证码不能为空" in HTMLText:
            self.formatPrint("验证码不能为空，如看不清请刷新！！", level="WARNING")
        elif "验证码不正确" in HTMLText:
            self.formatPrint("验证码不正确！！", level="WARNING")
        else:
            print(HTMLText)
            with open("./error/" + str(time.time()).split(".")[0] + ".html", "w") as f:
                f.write(HTMLText)
            self.formatPrint("未知类型错误，已打印出html并保存，请查看。", level="WARNING")

    def printMenu(self):
        def printEachMenu(Num, each):
            print("{:<2}{:>2}{:^22}".format("|", Num, each))

        menuList = ["学生个人课程表", "体育选修课报名"]
        print("==============================")
        print("{:<2}{:^26}{:>2}".format("|", "MENU", "|"))
        print("==============================")
        for i in range(len(menuList)):
            printEachMenu(i, menuList[i])
        print("{:<2}{:>2}{:^26}".format("|", -1, "Login Out"))
        print("==============================")

if __name__ == '__main__':
    aCommandUI = CommandUI()

    aCommandUI.welcome()

    loginFlag = False
    welcomeInfo = "undefine"
    token = None
    hiddenValue = None
    personName = None

    while(not loginFlag):
        tempflag = None
        if not username:
            username = input("请输入学号:\n>>> ")
        else:
            tempflag = input("检测到用户名，为 {}，是否更换用户名(y/n)\n>>> ".format(username))
            if judgeTempFlag(tempflag):
                username = input("请输入学号:\n>>> ")
            else:
                pass

        if not password or tempflag:
            password = input("请输入密码:\n>>> ")

        aCommandUI.formatPrint("正在登陆中,请稍后")

        info = getHiddenValueAndToken()         # 获取 __VIEWSTATE 和 会话token
        hiddenValue = info['hidenValue']        # __VIEWSTATE
        token = info['token']                   # 会话token

        # 拼装链接
        checkCodeUrl = "http://jw.hljit.edu.cn/(" + str(token) + ")/CheckCode.aspx"
        loginUrl = "http://jw.hljit.edu.cn/(" + str(token) + ")/default2.aspx"

        veriCode = getVeriCode(checkCodeUrl)    # 请求并识别验证码

        # 判断信息获取完全
        if hiddenValue and veriCode and token:
            # 组合登陆表单
            data["__VIEWSTATE"] = hiddenValue
            data["txtSecretCode"] = veriCode
            data["txtUserName"] = username
            data["TextBox2"] = password
            response = requests.post(loginUrl, data, headers)
            response.encoding = response.apparent_encoding
            # print("veriCode:" + str(veriCode))
            # print(response.url)

            soup = BeautifulSoup(response.text, "html.parser")
            infoBox = soup.find(name="div", attrs={'class': 'info'})
            if infoBox:
                welcomeInfo = infoBox.text
                welcomeInfo = welcomeInfo.replace("\n", "").replace("退出", "")
                aCommandUI.formatPrint(welcomeInfo)
                loginFlag = True
                break
            else:
                '''
                1. 用户名不存在或未按照要求参加教学活动！！
                2. 密码错误！！
                3. 验证码不能为空，如看不清请刷新！！
                4. 验证码不正确！！
                '''
                HTMLText = response.text
                aCommandUI.loginFail(HTMLText)
        else:
            aCommandUI.getLoginInfoFail(hiddenValue, veriCode, token)

    if loginFlag:
        aCommandUI.printMenu()
    while(loginFlag):
        # 获得学生姓名，获取信息时需要
        personName = welcomeInfo.replace("欢迎您：", "").replace("同学", "")
        # 缓存登陆日志到本地
        with open("./loginToken.dat", "a+") as f:
            f.write(str(time.time()).split(".")[0] + "  " + token + "  " + username + "\n")

        selectFlag = input("请选择相应的项目，并以数字输入:\n>>> ")
        if selectFlag == '-1':
            loginFlag = False
            loginOut(token, username, hiddenValue)
            break

        if selectFlag == '0':
            curriculum = getCurriculum(personName, token)
            if curriculum:
                with open("./curriculum.html", "w") as f:
                    f.write(str(curriculum))
                aCommandUI.formatPrint("获取课程表成功")
            else:
                aCommandUI.formatPrint("获取课程表失败")

            tempFlag = input("是否生成ICS文件(y/n):\n>>> ")
            if tempFlag.lower() == 'y' or tempFlag.lower() == 'yes':
                getIcs(curriculum, 'MyCurriculum')
                aCommandUI.formatPrint("生成 .ics 文件成功")
        elif selectFlag == '1':
            aCommandUI.formatPrint("该功能尚未开发完成，十分抱歉", level="ERROR")

    aCommandUI.formatPrint("再见 {} 同学".format(personName))
