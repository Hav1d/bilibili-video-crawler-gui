import os
import threading
import wx
import wx.html
import random
import json
import re
import pymysql
import time
import base64
import logging
import pprint
import joblib
import math
import asyncio
import aiohttp
import aiofiles
import requests as rq
from PIL import Image
from io import BytesIO
from urllib.parse import urlsplit
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from fake_useragent import UserAgent
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
import wx.grid as gridlib
import mplcursors
from pylab import mpl
# 设置显示中文字体
mpl.rcParams["font.sans-serif"] = ["SimHei"]


class MyHtmlWindow(wx.html.HtmlWindow):
    def __init__(self, *args, **kw):
        super(MyHtmlWindow, self).__init__(*args, **kw)

    def OnLinkClicked(self, link):
        wx.LaunchDefaultBrowser(link.GetHref())

# 登录
class MainFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(MainFrame, self).__init__(*args, **kw)
        self.panel = wx.Panel(self)
        self.title = wx.StaticText(self.panel, pos=(160, 50), label="Bilibili查询及预测系统")
        font = wx.Font(19, wx.DEFAULT, wx.FONTSTYLE_NORMAL, wx.NORMAL)
        font_label = wx.Font(18, wx.DEFAULT, wx.FONTSTYLE_NORMAL, wx.NORMAL)
        self.title.SetFont(font)
        self.account_label = wx.StaticText(self.panel, pos=(130, 150), label="Account")
        self.account_label.SetFont(font_label)
        self.account_text = wx.TextCtrl(self.panel, pos=(250, 150), size=(200, 29))
        self.password_label = wx.StaticText(self.panel, pos=(130, 200), label="Password")
        self.author_label = wx.StaticText(self.panel, pos=(500, 320), label="Author:何昊燃")
        self.password_label.SetFont(font_label)
        self.password_text = wx.TextCtrl(self.panel, pos=(250, 200), size=(200, 29), style=wx.TE_PASSWORD)
        self.login_button = wx.Button(self.panel, pos=(260, 240), label="Sign in", size=(100, 50))
        self.Root_button = wx.Button(self.panel, pos=(260, 300), label="管理员", size=(100, 50))
        self.login_button.SetFont(font)
        self.login_button.Bind(wx.EVT_BUTTON, self.on_login)
        self.Root_button.SetFont(font)
        self.Root_button.Bind(wx.EVT_BUTTON, self.on_Root)
        self.SetSize((600, 400))
        self.SetTitle("Bilibili视频平台数据获取及预测系统V1.0")

        MainFrame.xy(self)

    def on_login(self, event):
        account_number = self.account_text.GetValue()
        password_number = self.password_text.GetValue()
        conn = MainFrame.get_connect_with_mysql()
        cur = conn.cursor()
        sql = """SELECT * FROM user WHERE account = %s;
                            """
        cur.execute(sql, (account_number,))
        rows = cur.fetchall()
        if not rows:
            wx.MessageBox("登录失败,请重新输入。", "Failure", wx.OK | wx.ICON_WARNING)
        else:
            if rows[0]['password'] == password_number:
                wx.MessageBox("登录成功", "Congratulations", wx.OK)
                connection = MainFrame.get_connect_with_mysql()
                try:
                    with connection.cursor() as cursor:
                        # 检查表是否存在，如果不存在则创建
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS Down (
                                account_name VARCHAR(255),
                                login_time VARCHAR(255)
                            )
                        """)
                        # 插入数据
                        sql = """INSERT INTO Down (account_name, login_time)
                                     VALUES (%s, %s)"""
                        cursor.execute(sql, (
                                account_number, datetime.now()
                            ))
                    connection.commit()
                finally:
                    connection.close()
                self.Hide()
                self.search_frame = SearchFrame(None)
                self.search_frame.Show()
            else:
                wx.MessageBox("登录失败,请重新输入。", "Failure", wx.OK | wx.ICON_WARNING)

    def on_Root(self, event):
        account_number = self.account_text.GetValue()
        password_number = self.password_text.GetValue()
        conn = MainFrame.get_connect_with_mysql()
        cur = conn.cursor()
        sql = """SELECT * FROM root WHERE account = %s;"""
        cur.execute(sql, (account_number,))
        rows = cur.fetchall()
        if not rows:
            wx.MessageBox("登录失败,请重新输入。", "Failure", wx.OK | wx.ICON_WARNING)
        else:
            if rows[0]['password'] == password_number:
                wx.MessageBox("登录成功", "Congratulations", wx.OK)
                self.Hide()
                wx.CallAfter(self.show_root_frame)
            else:
                wx.MessageBox("登录失败,请重新输入。", "Failure", wx.OK | wx.ICON_WARNING)

    def show_root_frame(self):
        self.root_frame = RootFrame(self)
        self.root_frame.Show()

    @staticmethod
    def xy(self):
        screen_size = wx.DisplaySize()
        window_size = self.GetSize()
        x = (screen_size[0] - window_size[0]) // 2
        y = (screen_size[1] - window_size[1]) // 2
        self.SetPosition((x, y))

    @staticmethod
    def get_connect_with_mysql():
        conn = pymysql.connect(
            host='localhost',
            port=3306,
            user='root',
            password='1234567',
            db='world',
            charset='utf8mb4',  # 使用 utf8mb4 字符集
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn

    @staticmethod
    def compress_image(image_path, max_size=1024):
        try:
            img = Image.open(image_path)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.thumbnail((max_size, max_size), Image.ANTIALIAS)
            img.save(image_path, optimize=True, quality=85)
        except Exception as e:
            print(f"Error compressing image {image_path}: {e}")

    @staticmethod
    def process_url(url):
        if not url.startswith(('http://', 'https://')):
            return 'https:' + url
        return url

    @staticmethod
    async def download_image(url, save_dir='images'):
        url = MainFrame.process_url(url)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        local_filename = os.path.join(save_dir, os.path.basename(urlsplit(url).path))
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    async with aiofiles.open(local_filename, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
            await MainFrame.resize_image(local_filename, 100)
            return local_filename
        except aiohttp.ClientError as e:
            print(f"Error downloading {url}: {e}")
            return None

    @staticmethod
    async def resize_image(image_path, max_size):
        try:
            # 同步操作：读取和处理图像
            with Image.open(image_path) as img:
                img.thumbnail((max_size, max_size), Image.LANCZOS)
                img.save(image_path)
        except Exception as e:
            print(f"Error resizing image {image_path}: {e}")

# 照片下载
class ImageDownloader(threading.Thread):
    def __init__(self, url, save_path):
        threading.Thread.__init__(self)
        self.url = url
        self.save_path = save_path

    def run(self):
        self.url = MainFrame.process_url(self.url)
        try:
            response = rq.get(self.url, stream=True)
            if response.status_code == 200:
                try:
                    image = Image.open(BytesIO(response.content))
                    image.verify()
                    with open(self.save_path, 'wb') as f:
                        f.write(response.content)
                    print(f"Downloaded {self.url}")
                except Exception as e:
                    print(f"Image verification failed for {self.url}: {e}")
            else:
                print(f"Failed to download {self.url}")
        except Exception as e:
            print(f"Error downloading {self.url}: {e}")

# 排序
class SearchFrame(wx.Frame):

    def __init__(self, *args, **kw):
        super(SearchFrame, self).__init__(*args, **kw)
        self.panel = wx.Panel(self)
        self.html_win = MyHtmlWindow(self.panel, style=wx.NO_BORDER)
        self.html_win.SetStandardFonts()

        self.items = []

        # 设置字体
        font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        button_font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

        # 设置搜索框和页数框
        self.search_text = wx.TextCtrl(self.panel, pos=(50, 10), size=(300, 28), value="搜索关键词")
        self.search_text.SetFont(font)
        self.pp_text = wx.TextCtrl(self.panel, pos=(50, 60), size=(300, 28), value="页数")
        self.pp_text.SetFont(font)

        # 设置排序选择
        self.sort_choices = ['视频时长', '点赞数', '收藏数', '弹幕数', '播放量', '评论数']
        self.sort_choice = wx.Choice(self.panel, pos=(50, 110), choices=self.sort_choices, size=(300, 40))
        self.sort_choice.SetFont(font)
        self.sort_choice.SetSelection(0)

        # 设置按钮
        search_button = wx.Button(self.panel, pos=(370, 10), label="搜索", size=(120, 40))
        search_button.SetFont(button_font)
        sort_button = wx.Button(self.panel, pos=(370, 110), label="排序", size=(120, 40))
        sort_button.SetFont(button_font)
        exit_button = wx.Button(self.panel, pos=(500, 110), label="退出", size=(120, 40))
        exit_button.SetFont(button_font)
        prediction_button = wx.Button(self.panel, pos=(500, 60), label="数据及预测", size=(120, 40))
        prediction_button.SetFont(button_font)
        back_to_login_button = wx.Button(self.panel, pos=(50, 160), label="返回登陆窗口", size=(250, 40))
        back_to_login_button.SetFont(button_font)

        # 绑定事件
        search_button.Bind(wx.EVT_BUTTON, self.on_search)
        sort_button.Bind(wx.EVT_BUTTON, self.on_sortt)
        exit_button.Bind(wx.EVT_BUTTON, self.on_exit)
        prediction_button.Bind(wx.EVT_BUTTON, self.on_prediction)
        back_to_login_button.Bind(wx.EVT_BUTTON, self.on_back_to_login)

        # 布局管理
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.search_text, 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(self.pp_text, 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(self.sort_choice, 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(search_button, 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(sort_button, 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(prediction_button, 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(exit_button, 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(back_to_login_button, 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(self.html_win, 1, wx.EXPAND | wx.ALL, 10)
        self.panel.SetSizer(sizer)

        # 设置窗口标题和大小
        self.SetTitle("Bilibili视频平台数据获取及预测系统V1.0")
        self.SetSize((900, 900))
        MainFrame.xy(self)

    def on_exit(self, event):
        self.Close()

    def on_prediction(self, event):
        self.Hide()
        self.prediction_frame = PredictionFrame(self, self.items)
        self.prediction_frame.Show()

    def on_back_to_login(self, event):
        self.Close()
        self.login_frame = MainFrame(None)
        self.login_frame.Show()

    def on_search(self, event):
        search = self.search_text.GetValue()
        pp = self.pp_text.GetValue()
        search_results = self.search(search, pp)
        self.display(search_results)

    def time_to_minutes(self, time_str):
        try:
            minutes, seconds = map(int, time_str.strip().split(':'))
            return minutes * 60 + seconds
        except ValueError:
            return None

    def on_sortt(self, event):
        canshu = self.sort_choice.GetStringSelection()
        try:
            if canshu == '视频时长':
                # 过滤掉无效的时间格式并标记直播间
                for item in self.items:
                    item['时间值'] = self.time_to_minutes(item['视频时长'])

                valid_items = [item for item in self.items if item['时间值'] is not None]
                live_items = [item for item in self.items if item['时间值'] is None]

                sorted_canshu = sorted(valid_items, key=lambda x: x['时间值'])
            else:
                valid_items = [item for item in self.items if item.get(canshu) is not None]
                live_items = [item for item in self.items if item.get(canshu) is None]

                sorted_canshu = sorted(valid_items, key=lambda x: x[canshu], reverse=True)

            html_content = f"<h3>按{canshu}排序:</h3><ul>"

            for video in sorted_canshu + live_items:  # 将直播间视频放在最后
                if isinstance(video, dict):
                    title = video.get('标题', '未知标题')
                    website = video.get('视频网站', '未知网站')
                    if canshu == '视频时长':
                        additional_info = video['视频时长'] if video['时间值'] is not None else '直播间'
                    else:
                        additional_info = video.get(canshu, '直播间')
                        if video.get(canshu) is None:  # 标记直播间
                            additional_info = '直播间'
                    html_content += f'<li>标题: {title}, {canshu}: {additional_info}, <a href="{website}">视频网站</a></li>'
            html_content += "</ul>"

            print(html_content)  # 打印生成的 HTML 内容用于调试

            self.html_win.SetPage(html_content)
        except ValueError as e:
            wx.MessageBox(f"排序过程中发生错误: {e}", "错误", wx.OK | wx.ICON_WARNING)

    def search(self, search, pp):
        search_results = []
        ua = UserAgent()
        try:
            pp = int(pp) + 1
        except Exception as e:
            wx.MessageBox(f"请输入正确的页数", "错误", wx.OK | wx.ICON_WARNING)
        for pps in range(1, pp):
            print(pps)
            url = f'https://api.bilibili.com/x/web-interface/search/all/v2?page={pps}&keyword={search}'
            user_agents = [ua.ie, ua.opera, ua.chrome, ua.firefox, ua.safari]
            headers = {
                'User-Agent': random.choice(user_agents),
                'Cookie': 'your_cookie_here'
            }
            try:
                response = rq.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                json_data = response.json()
                if 'data' in json_data and 'result' in json_data['data']:
                    result = json_data['data']['result']
                    if len(result) > 11 and 'data' in result[11]:
                        search_results.append(result[11]['data'])
            except (rq.RequestException, KeyError, IndexError) as e:
                wx.MessageBox(f"搜索过程中发生错误: {e}", "错误", wx.OK | wx.ICON_WARNING)
                break
        return search_results

    def search_display(self):
        html_content = "<h3>正常排序:</h3><ul>"
        for video in self.items:
            if isinstance(video, dict):

                title = video.get('标题', '未知标题')
                website = video.get('视频网站', '未知网站')
                pic = video.get('视频封面', '')
                if pic:
                    pic = os.path.join('images', os.path.basename(pic))
                    pic_tag = f'<img src="file:///{os.path.abspath(pic)}" width="100">'
                else:
                    pic_tag = '无封面'
                # html_content += f'<li>{pic_tag}<br>标题: {title}, <a href="{website}">视频网站</a></li>'
                html_content += f'''
                            <li>
                                {pic_tag}<br>标题: {title}, <a href="{website}">视频网站</a>
                                <br>
                                视频时长: {video.get('视频时长', '未知时长')}
                                <br>
                                视频分类: {video.get('视频分类', '未知分类')}
                                <br>
                                aid: {video.get('aid', '未知')}
                                <br>
                                视频标签: {video.get('视频标签', '无')}
                                <br>
                                bvid: {video.get('bvid', '未知')}
                                <br>
                                视频描述: {video.get('视频描述', '')}
                                <br>
                                up主: {video.get('up主', '未知作者')}
                                <br>
                                收藏数: {video.get('收藏数', 0)}
                                <br>
                                弹幕数: {video.get('弹幕数', 0)}
                                <br>
                                点赞数: {video.get('点赞数', 0)}
                                <br>
                                播放量: {video.get('播放量', 0)}
                                <br>
                                评论数: {video.get('评论数', 0)}
                                <br>
                                video评论数: {video.get('video评论数', 0)}
                            </li>
                            '''

        html_content += "</ul>"

        print(html_content)  # 打印生成的 HTML 内容用于调试

        self.html_win.SetPage(html_content)

    def sortt(self, event):
        canshu = self.sort_choice.GetStringSelection()
        if canshu == '视频时长':
            sorted_canshu = sorted(self.items, key=lambda x: self.time_to_minutes(x['视频时长']))
        else:
            sorted_canshu = sorted(self.items, key=lambda x: x.get(canshu, 0), reverse=True)

        html_content = f"<h3>按{canshu}排序:</h3><ul>"
        for video in sorted_canshu:
            if isinstance(video, dict):
                title = video.get('标题', '未知标题')
                website = video.get('视频网站', '未知网站')
                additional_info = video.get(canshu, '') if canshu != '视频时长' else video['视频时长']
                html_content += f'<li>标题: {title}, {canshu}: {additional_info}, <a href="{website}">视频网站</a></li>'
        html_content += "</ul>"

        # 打印生成的 HTML 内容用于调试
        print(html_content)

        self.html_win.SetPage(html_content)

    def display(self, a):
        self.items = []
        loop = asyncio.get_event_loop()
        tasks = []

        for item_list in a:
            if isinstance(item_list, list):
                for data in item_list:
                    if isinstance(data, dict):
                        item = {
                            '标题': str(data.get('title', '')).replace('<em class="keyword">', '').replace("</em>", '').replace('&#x27;', "'").replace('\u3000', "").replace('&amp;', '&'),
                            '视频分类': data.get('typename', '未知分类'),
                            '视频网站': data.get('arcurl', '未知网站'),
                            'aid': data.get('aid', '未知'),
                            '视频标签': data.get('tag', '无'),
                            'bvid': data.get('bvid', '未知'),
                            '视频描述': str(data.get('description', '')).replace('\n', '').replace('&#x27;', "'").replace('\u3000', "").replace('&amp;', '&'),
                            '视频时长': data.get('duration', '未知时长'),
                            '视频封面': data.get('pic', ''),
                            'up主': data.get('author', '未知作者'),
                            '收藏数': data.get('favorites', 0),
                            '弹幕数': data.get('danmaku', 0),
                            '点赞数': data.get('like', 0),
                            '播放量': data.get('play', 0),
                            '评论数': data.get('review', 0),
                            'video评论数': data.get('video_review', 0)
                        }
                        self.items.append(item)
                        if '视频封面' in item and item['视频封面']:
                            tasks.append(MainFrame.download_image(item['视频封面']))

        loop.run_until_complete(asyncio.gather(*tasks))
        self.search_display()

# 管理员
class RootFrame(wx.Frame):

    def __init__(self, parent, *args, **kw):
        super(RootFrame, self).__init__(parent, *args, **kw)
        self.parent = parent  # 存储父窗口

        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(wx.Colour(255, 255, 255))  # 设置背景颜色为白色

        self.title = wx.StaticText(self.panel, label="Root管理员", style=wx.ALIGN_CENTER)
        font = wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.title.SetFont(font)

        button_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        login_log_button = wx.Button(self.panel, label='登录日志', size=(200, 50))
        login_log_button.SetFont(button_font)
        search_log_button = wx.Button(self.panel, label='搜索查询日志', size=(200, 50))
        search_log_button.SetFont(button_font)
        prediction_log_button = wx.Button(self.panel, label='预测日志', size=(200, 50))
        prediction_log_button.SetFont(button_font)
        account_management_button = wx.Button(self.panel, label='账户密码管理', size=(200, 50))
        account_management_button.SetFont(button_font)
        super_admin_management_button = wx.Button(self.panel, label='超级管理员管理', size=(200, 50))
        super_admin_management_button.SetFont(button_font)
        back_button = wx.Button(self.panel, label='返回登录', size=(200, 50))
        back_button.SetFont(button_font)

        # 绑定按钮事件
        login_log_button.Bind(wx.EVT_BUTTON, self.on_login_log)
        search_log_button.Bind(wx.EVT_BUTTON, self.on_search_log)
        prediction_log_button.Bind(wx.EVT_BUTTON, self.on_prediction_log)
        account_management_button.Bind(wx.EVT_BUTTON, self.on_account_management)
        super_admin_management_button.Bind(wx.EVT_BUTTON, self.on_super_admin_management)
        back_button.Bind(wx.EVT_BUTTON, self.on_back_to_login)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.title, 0, wx.ALIGN_CENTER | wx.ALL, 20)
        sizer.Add(login_log_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.Add(search_log_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.Add(prediction_log_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.Add(account_management_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.Add(super_admin_management_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.Add(back_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        self.panel.SetSizer(sizer)

        self.SetTitle("Bilibili视频平台数据获取及预测系统V1.0")
        self.SetSize((500, 700))

        MainFrame.xy(self)

    def on_super_admin_management(self, event):
        account_number = self.parent.account_text.GetValue()
        password_number = self.parent.password_text.GetValue()
        conn = MainFrame.get_connect_with_mysql()
        cur = conn.cursor()
        sql = """SELECT * FROM super_root WHERE account = %s;"""
        cur.execute(sql, (account_number,))
        rows = cur.fetchall()
        if not rows:
            wx.MessageBox("没有权限访问超级管理员功能。", "Failure", wx.OK | wx.ICON_WARNING)
        else:
            if rows[0]['password'] == password_number:
                wx.MessageBox("进入超级管理员管理。", "Success", wx.OK)
                self.Hide()
                self.SuperAdminFrame = SuperAdminFrame(self)
                self.SuperAdminFrame.Show()
            else:
                wx.MessageBox("没有权限访问超级管理员功能。", "Failure", wx.OK | wx.ICON_WARNING)

    def on_login_log(self, event):
        conn = MainFrame.get_connect_with_mysql()
        cur = conn.cursor()
        cur.execute("SELECT account_name, login_time FROM Down")
        rows = cur.fetchall()
        account_info = "\n".join([f"账户名称: {row['account_name']} 登陆时间: {row['login_time']}" for row in rows])
        wx.MessageBox(account_info, "查看账户密码", wx.OK | wx.ICON_INFORMATION)
        cur.close()
        conn.close()

    def on_search_log(self, event):
        conn = MainFrame.get_connect_with_mysql()
        cur = conn.cursor()
        cur.execute("SELECT Text, Page, Time FROM search")
        rows = cur.fetchall()
        account_info = "\n".join([f"搜索关键词: {row['Text']} 页数 {row['Page']} 搜索时间: {row['Time']}" for row in rows])
        wx.MessageBox(account_info, "查看搜索记录", wx.OK | wx.ICON_INFORMATION)
        cur.close()
        conn.close()

    def on_prediction_log(self, event):
        conn = MainFrame.get_connect_with_mysql()
        cur = conn.cursor()
        cur.execute("SELECT 视频标题, bvid FROM video_details")
        rows = cur.fetchall()
        account_info = "\n".join([f"视频标题: {row['视频标题']} bvid: {row['bvid']}" for row in rows])
        wx.MessageBox(account_info, "查看预测", wx.OK | wx.ICON_INFORMATION)
        cur.close()
        conn.close()

    def on_account_management(self, event):
        self.Hide()
        AccountManagementFrame(self).Show()

    def on_back_to_login(self, event):
        self.Close()
        self.login_frame = MainFrame(None)
        self.login_frame.Show()

    def update_choices(self):
        conn = MainFrame.get_connect_with_mysql()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT account FROM user")
                rows = cur.fetchall()
                print(rows)  # [{'account': '1'}, {'account': 'Havid'}]
                accounts = [row['account'] for row in rows]  # 使用字典键来访问数据
                self.choice.Clear()
                self.choice.Append(accounts)
        finally:
            conn.close()

# 账户管理
class AccountManagementFrame(wx.Frame):

    def __init__(self, parent, *args, **kw):
        super(AccountManagementFrame, self).__init__(parent, *args, **kw)
        self.parent = parent

        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(wx.Colour(255, 255, 255))  # 设置背景颜色为白色

        self.title = wx.StaticText(self.panel, label="账户管理", style=wx.ALIGN_CENTER)
        font = wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.title.SetFont(font)

        choice_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.choice = wx.Choice(self.panel, size=(250, 40))
        self.choice.SetFont(choice_font)
        self.update_choices()

        button_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        self.modify_button = wx.Button(self.panel, label='修改', size=(200, 50))
        self.modify_button.SetFont(button_font)
        self.delete_button = wx.Button(self.panel, label='删除', size=(200, 50))
        self.delete_button.SetFont(button_font)
        self.back_button = wx.Button(self.panel, label='返回上一级', size=(200, 50))
        self.back_button.SetFont(button_font)
        self.exit_button = wx.Button(self.panel, label='退出程序', size=(200, 50))
        self.exit_button.SetFont(button_font)
        self.add_button = wx.Button(self.panel, label='新增账户', size=(200, 50))
        self.add_button.SetFont(button_font)

        self.add_button.Bind(wx.EVT_BUTTON, self.on_add)
        self.modify_button.Bind(wx.EVT_BUTTON, self.on_modify)
        self.delete_button.Bind(wx.EVT_BUTTON, self.on_delete)
        self.back_button.Bind(wx.EVT_BUTTON, self.on_back)
        self.exit_button.Bind(wx.EVT_BUTTON, self.on_exit)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.title, 0, wx.ALIGN_CENTER | wx.ALL, 20)
        sizer.Add(self.choice, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.Add(self.modify_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.Add(self.delete_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.Add(self.back_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.Add(self.exit_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.Add(self.add_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        self.panel.SetSizer(sizer)

        self.SetTitle("Bilibili视频平台数据获取及预测系统V1.0")
        self.SetSize((500, 700))

        MainFrame.xy(self)

    def update_choices(self):
        conn = MainFrame.get_connect_with_mysql()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT account FROM user")
                rows = cur.fetchall()
                print(rows)  # [{'account': '1'}, {'account': 'Havid'}]
                accounts = [row['account'] for row in rows]  # 使用字典键来访问数据
                self.choice.Clear()
                self.choice.Append(accounts)
        finally:
            conn.close()

    def on_modify(self, event):
        selected_account = self.choice.GetStringSelection()
        if not selected_account:
            wx.MessageBox("请选择一个账户进行修改", "提示", wx.OK | wx.ICON_WARNING)
            return
        ModifyAccountFrame(self, selected_account).Show()

    def on_delete(self, event):
        selected_account = self.choice.GetStringSelection()
        if not selected_account:
            wx.MessageBox("请选择一个账户进行删除", "提示", wx.OK | wx.ICON_WARNING)
            return

        conn = MainFrame.get_connect_with_mysql()
        cur = conn.cursor()
        cur.execute("DELETE FROM user WHERE account = %s", (selected_account,))
        conn.commit()
        cur.close()
        conn.close()
        self.update_choices()
        wx.MessageBox(f"账户 {selected_account} 已删除", "提示", wx.OK | wx.ICON_INFORMATION)

    def on_back(self, event):
        self.Close()
        self.parent.Show()

    def on_exit(self, event):
        self.Close()
        wx.Exit()

    def on_add(self, event):
        AddAccountFrame(self).Show()

# 超级管理员
class SuperAdminFrame(wx.Frame):

    def __init__(self, parent, *args, **kw):
        super(SuperAdminFrame, self).__init__(parent, *args, **kw)
        self.parent = parent
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(wx.Colour(255, 255, 255))  # 设置背景颜色为白色

        self.title = wx.StaticText(self.panel, label="超级管理员", style=wx.ALIGN_CENTER)
        font = wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.title.SetFont(font)

        choice_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.choice = wx.Choice(self.panel, size=(250, 40))
        self.choice.SetFont(choice_font)
        self.update_choices()

        button_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        view_accounts_button = wx.Button(self.panel, label='查看管理员', size=(200, 50))
        view_accounts_button.SetFont(button_font)
        modify_accounts_button = wx.Button(self.panel, label='修改管理员', size=(200, 50))
        modify_accounts_button.SetFont(button_font)
        self.back_button = wx.Button(self.panel, label='返回上一级', size=(200, 50))
        self.back_button.SetFont(button_font)
        self.exit_button = wx.Button(self.panel, label='退出程序', size=(200, 50))
        self.exit_button.SetFont(button_font)

        view_accounts_button.Bind(wx.EVT_BUTTON, self.on_view_accounts)
        modify_accounts_button.Bind(wx.EVT_BUTTON, self.on_modify_accounts)
        self.back_button.Bind(wx.EVT_BUTTON, self.on_back)
        self.exit_button.Bind(wx.EVT_BUTTON, self.on_exit)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.title, 0, wx.ALIGN_CENTER | wx.ALL, 20)
        sizer.Add(self.choice, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.Add(view_accounts_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.Add(modify_accounts_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.Add(self.back_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.Add(self.exit_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        self.panel.SetSizer(sizer)

        self.SetTitle("Bilibili视频平台数据获取及预测系统V1.0")
        self.SetSize((500, 600))

        MainFrame.xy(self)

    def update_choices(self):
        conn = MainFrame.get_connect_with_mysql()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT account FROM root")
                rows = cur.fetchall()
                print(rows)  # [{'account': '1'}, {'account': 'Havid'}]
                accounts = [row['account'] for row in rows]  # 使用字典键来访问数据
                self.choice.Clear()
                self.choice.Append(accounts)
        finally:
            conn.close()

    def on_view_accounts(self, event):
        conn = MainFrame.get_connect_with_mysql()
        cur = conn.cursor()
        cur.execute("SELECT account, password FROM root")
        rows = cur.fetchall()
        account_info = "\n".join([f"Account: {row['account']}, Password: {row['password']}" for row in rows])
        wx.MessageBox(account_info, "查看账户密码", wx.OK | wx.ICON_INFORMATION)
        cur.close()
        conn.close()

    def on_modify_accounts(self, event):
        selected_account = self.choice.GetStringSelection()
        if not selected_account:
            wx.MessageBox("请先选择一个账号", "提示", wx.OK | wx.ICON_WARNING)
            return
        SuperModify(self, selected_account).Show()

    def on_back(self, event):
        self.Close()
        self.parent.Show()

    def on_exit(self, event):
        self.Close()

# 超级管理修改密码
class SuperModify(wx.Frame):

    def __init__(self, parent, account, *args, **kw):
        super(SuperModify, self).__init__(parent, *args, **kw)
        self.parent = parent
        self.account = account

        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(wx.Colour(255, 255, 255))  # 设置背景颜色为白色

        self.title = wx.StaticText(self.panel, label=f"修改账户: {self.account}", style=wx.ALIGN_CENTER)
        title_font = wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.title.SetFont(title_font)

        label_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        self.new_account_label = wx.StaticText(self.panel, label="新账号:")
        self.new_account_label.SetFont(label_font)
        self.new_account_text = wx.TextCtrl(self.panel, size=(250, 30))

        self.new_password_label = wx.StaticText(self.panel, label="新密码:")
        self.new_password_label.SetFont(label_font)
        self.new_password_text = wx.TextCtrl(self.panel, size=(250, 30), style=wx.TE_PASSWORD)

        button_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        self.modify_button = wx.Button(self.panel, label='确认修改', size=(200, 40))
        self.modify_button.SetFont(button_font)
        self.cancel_button = wx.Button(self.panel, label='取消', size=(200, 40))
        self.cancel_button.SetFont(button_font)

        self.modify_button.Bind(wx.EVT_BUTTON, self.on_modify)
        self.cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)

        # 布局
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.title, 0, wx.ALIGN_CENTER | wx.ALL, 20)

        grid_sizer = wx.GridBagSizer(10, 10)
        grid_sizer.Add(self.new_account_label, pos=(0, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.new_account_text, pos=(0, 1))
        grid_sizer.Add(self.new_password_label, pos=(1, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.new_password_text, pos=(1, 1))

        sizer.Add(grid_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.modify_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        button_sizer.Add(self.cancel_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        self.panel.SetSizer(sizer)

        self.SetTitle("修改账户")
        self.SetSize((500, 300))

        MainFrame.xy(self)

    def on_modify(self, event):
        new_account = self.new_account_text.GetValue()
        new_password = self.new_password_text.GetValue()
        if not new_account or not new_password:
            wx.MessageBox("账号和密码不能为空", "提示", wx.OK | wx.ICON_WARNING)
            return

        conn = MainFrame.get_connect_with_mysql()
        cur = conn.cursor()
        cur.execute("SELECT account FROM root WHERE account=%s", (new_account,))
        if cur.fetchone():
            wx.MessageBox("账号已存在，请选择其他账号", "提示", wx.OK | wx.ICON_WARNING)
            cur.close()
            conn.close()
            return

        cur.execute("UPDATE root SET account=%s, password=%s WHERE account=%s", (new_account, new_password, self.account))
        conn.commit()
        cur.close()
        conn.close()

        wx.MessageBox(f"账户 {self.account} 已修改", "提示", wx.OK | wx.ICON_INFORMATION)
        self.Close()
        self.parent.update_choices()

    def on_cancel(self, event):
        self.Close()

# 预测主窗口
class PredictionFrame(wx.Frame):

    def __init__(self, parent, items):
        super(PredictionFrame, self).__init__(parent)
        self.parent = parent
        self.items = items

        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(wx.Colour(255, 255, 255))  # 设置背景颜色为白色

        self.title = wx.StaticText(self.panel, label="数据及预测", style=wx.ALIGN_CENTER)
        font = wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.title.SetFont(font)

        button_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        prediction_button = wx.Button(self.panel, label="热度预测", size=(150, 50))
        prediction_button.SetFont(button_font)
        comparison_button = wx.Button(self.panel, label="热度比较", size=(150, 50))
        comparison_button.SetFont(button_font)
        back_button = wx.Button(self.panel, label="返回上一级", size=(150, 50))
        back_button.SetFont(button_font)
        exit_button = wx.Button(self.panel, label="退出", size=(150, 50))
        exit_button.SetFont(button_font)

        prediction_button.Bind(wx.EVT_BUTTON, self.on_prediction)
        comparison_button.Bind(wx.EVT_BUTTON, self.on_comparison)
        back_button.Bind(wx.EVT_BUTTON, self.on_back)
        exit_button.Bind(wx.EVT_BUTTON, self.on_exit)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.title, 0, wx.ALIGN_CENTER | wx.ALL, 20)
        sizer.Add(prediction_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.Add(comparison_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.Add(back_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.Add(exit_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        self.panel.SetSizer(sizer)

        self.SetTitle("Bilibili视频平台数据获取及预测系统V1.0")
        self.SetSize((500, 500))

        MainFrame.xy(self)

    def on_prediction(self, event):
        self.Hide()
        self.prediction_select_frame = PredictionSelectFrame(self, self.items)
        self.prediction_select_frame.Show()

    def on_comparison(self, event):
        self.Hide()
        self.comparison_frame = ComparisonFrame(self, self.items)
        self.comparison_frame.Show()

    def on_back(self, event):
        self.Close()
        self.parent.Show()

    def on_exit(self, event):
        self.Close()
        self.parent.Close()

# 新增账户
class AddAccountFrame(wx.Frame):
    def __init__(self, parent, *args, **kw):
        super(AddAccountFrame, self).__init__(parent, *args, **kw)
        self.parent = parent

        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(wx.Colour(255, 255, 255))  # 设置背景颜色为白色

        self.title = wx.StaticText(self.panel, label="新增账户", style=wx.ALIGN_CENTER)
        title_font = wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.title.SetFont(title_font)

        label_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        self.account_label = wx.StaticText(self.panel, label="账号:")
        self.account_label.SetFont(label_font)
        self.account_text = wx.TextCtrl(self.panel, size=(250, 30))

        self.password_label = wx.StaticText(self.panel, label="密码:")
        self.password_label.SetFont(label_font)
        self.password_text = wx.TextCtrl(self.panel, size=(250, 30), style=wx.TE_PASSWORD)

        button_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        self.add_button = wx.Button(self.panel, label='确认新增', size=(200, 40))
        self.add_button.SetFont(button_font)
        self.cancel_button = wx.Button(self.panel, label='取消', size=(200, 40))
        self.cancel_button.SetFont(button_font)

        self.add_button.Bind(wx.EVT_BUTTON, self.on_add)
        self.cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)

        # 布局
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.title, 0, wx.ALIGN_CENTER | wx.ALL, 20)

        grid_sizer = wx.GridBagSizer(10, 10)
        grid_sizer.Add(self.account_label, pos=(0, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.account_text, pos=(0, 1))
        grid_sizer.Add(self.password_label, pos=(1, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.password_text, pos=(1, 1))

        sizer.Add(grid_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.add_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        button_sizer.Add(self.cancel_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        self.panel.SetSizer(sizer)

        self.SetTitle("新增账户")
        self.SetSize((500, 300))

        MainFrame.xy(self)

    def on_add(self, event):
        new_account = self.account_text.GetValue()
        new_password = self.password_text.GetValue()
        if not new_account or not new_password:
            wx.MessageBox("账号和密码不能为空", "提示", wx.OK | wx.ICON_WARNING)
            return

        conn = MainFrame.get_connect_with_mysql()
        cur = conn.cursor()
        cur.execute("INSERT INTO user (account, password) VALUES (%s, %s)", (new_account, new_password))
        conn.commit()
        cur.close()
        conn.close()

        wx.MessageBox(f"账户 {new_account} 已新增", "提示", wx.OK | wx.ICON_INFORMATION)
        self.Close()
        self.parent.update_choices()

    def on_cancel(self, event):
        self.Close()

# 修改账户
class ModifyAccountFrame(wx.Frame):

    def __init__(self, parent, account, *args, **kw):
        super(ModifyAccountFrame, self).__init__(parent, *args, **kw)
        self.parent = parent
        self.account = account

        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(wx.Colour(255, 255, 255))  # 设置背景颜色为白色

        self.title = wx.StaticText(self.panel, label=f"修改账户: {self.account}", style=wx.ALIGN_CENTER)
        title_font = wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.title.SetFont(title_font)

        label_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        self.password_label = wx.StaticText(self.panel, label="新密码:")
        self.password_label.SetFont(label_font)
        self.password_text = wx.TextCtrl(self.panel, size=(250, 30), style=wx.TE_PASSWORD)

        button_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        self.modify_button = wx.Button(self.panel, label='确认修改', size=(200, 40))
        self.modify_button.SetFont(button_font)
        self.cancel_button = wx.Button(self.panel, label='取消', size=(200, 40))
        self.cancel_button.SetFont(button_font)

        self.modify_button.Bind(wx.EVT_BUTTON, self.on_modify)
        self.cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)

        # 布局
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.title, 0, wx.ALIGN_CENTER | wx.ALL, 20)

        grid_sizer = wx.GridBagSizer(10, 10)
        grid_sizer.Add(self.password_label, pos=(0, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.password_text, pos=(0, 1))

        sizer.Add(grid_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.modify_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        button_sizer.Add(self.cancel_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        self.panel.SetSizer(sizer)

        self.SetTitle("修改账户密码")
        self.SetSize((500, 250))

        MainFrame.xy(self)

    def on_modify(self, event):
        new_password = self.password_text.GetValue()
        if not new_password:
            wx.MessageBox("新密码不能为空", "提示", wx.OK | wx.ICON_WARNING)
            return

        conn = MainFrame.get_connect_with_mysql()
        cur = conn.cursor()
        cur.execute("UPDATE user SET password = %s WHERE account = %s", (new_password, self.account))
        conn.commit()
        cur.close()
        conn.close()

        wx.MessageBox(f"账户 {self.account} 的密码已修改", "提示", wx.OK | wx.ICON_INFORMATION)
        self.Close()
        self.parent.update_choices()

    def on_cancel(self, event):
        self.Close()

# 预测
class PredictionSelectFrame(wx.Frame):

    def __init__(self, parent, items):
        super(PredictionSelectFrame, self).__init__(parent)
        self.parent = parent
        self.items = items

        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(wx.Colour(255, 255, 255))  # 设置背景颜色为白色

        self.title = wx.StaticText(self.panel, label="选择视频进行热度预测", style=wx.ALIGN_CENTER)
        title_font = wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.title.SetFont(title_font)

        label_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        self.choice = wx.Choice(self.panel, size=(300, 50), choices=[item['标题'] for item in items])
        self.choice.SetFont(label_font)

        button_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        back_button = wx.Button(self.panel, label="返回", size=(200, 50))
        back_button.SetFont(button_font)
        exit_button = wx.Button(self.panel, label="退出", size=(200, 50))
        exit_button.SetFont(button_font)
        select_all_button = wx.Button(self.panel, label="全选预测", size=(250, 50))
        select_all_button.SetFont(button_font)
        start_prediction_button = wx.Button(self.panel, label="开始预测", size=(250, 50))
        start_prediction_button.SetFont(button_font)

        back_button.Bind(wx.EVT_BUTTON, self.on_back)
        exit_button.Bind(wx.EVT_BUTTON, self.on_exit)
        select_all_button.Bind(wx.EVT_BUTTON, self.on_select_all)
        start_prediction_button.Bind(wx.EVT_BUTTON, self.on_start_prediction)

        # 布局
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.title, 0, wx.ALIGN_CENTER | wx.ALL, 20)
        sizer.Add(self.choice, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(back_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        button_sizer.Add(exit_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        sizer.Add(select_all_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.Add(start_prediction_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        self.panel.SetSizer(sizer)

        self.SetTitle("Bilibili视频平台数据获取及预测系统V1.0")
        self.SetSize((500, 600))

        MainFrame.xy(self)

        # 加载训练好的模型
        self.model = joblib.load('video_popularity_model.pkl')

    def on_select_all(self, event):
        selected_items = [item['bvid'] for item in self.items]  # 选择所有视频
        self.fetch_and_insert_details(selected_items)

    def on_start_prediction(self, event):
        selected_index = self.choice.GetSelection()
        if selected_index != wx.NOT_FOUND:
            selected_items = [self.items[selected_index]['bvid']]
        else:
            wx.MessageBox("请选择一个视频进行预测", "提示", wx.OK | wx.ICON_INFORMATION)
            return
        self.fetch_and_insert_details(selected_items)

    def fetch_and_insert_details(self, bvids):
        data_list = []
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(self.fetch_video_details, bvid): bvid for bvid in bvids}
            for future in as_completed(futures):
                bvid = futures[future]
                try:
                    details, ctime, duration, title = future.result()
                    readable_ctime = datetime.fromtimestamp(ctime).strftime('%Y-%m-%d %H:%M:%S')
                    time_diff = datetime.now() - datetime.fromtimestamp(ctime)
                    duration_str = f"{duration // 60} 分 {duration % 60} 秒"
                    data_list.append({
                        "硬币数量": details['coin'],
                        "播放量": details['view'],
                        "发布时间": readable_ctime,
                        "发布时长": f"{time_diff.days} 天 {time_diff.seconds // 3600} 小时 {(time_diff.seconds // 60) % 60} 分钟",
                        "弹幕量": details['danmaku'],
                        "评论量": details['reply'],
                        "收藏量": details['favorite'],
                        "分享数": details['share'],
                        "点赞": details['like'],
                        "视频时长": duration_str,
                        "视频标题": title,
                        "bvid": bvid
                    })
                except Exception as e:
                    print(f"Error fetching details for {bvid}: {e}")

        self.insert_into_db(data_list)
        self.predict_and_show(data_list)

    def insert_into_db(self, data_list):
        connection = MainFrame.get_connect_with_mysql()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS video_details (
                        硬币数量 INT,
                        播放量 INT,
                        发布时间 DATETIME,
                        发布时长 VARCHAR(255),
                        弹幕量 INT,
                        评论量 INT,
                        收藏量 INT,
                        分享数 INT,
                        点赞 INT,
                        视频时长 VARCHAR(255),
                        视频标题 VARCHAR(255),
                        热度值 INT,
                        bvid VARCHAR(255)
                    )
                """)
                for data in data_list:
                    hot = self.count_arc_hot(
                        data["硬币数量"], data["收藏量"], data["弹幕量"],
                        data["评论量"], data["播放量"], data["点赞"],
                        data["分享数"], datetime.strptime(data["发布时间"], "%Y-%m-%d %H:%M:%S").timestamp()
                    )
                    sql = """INSERT INTO video_details (硬币数量, 播放量, 发布时间, 发布时长, 弹幕量, 评论量, 收藏量, 分享数, 点赞, 视频时长, 视频标题, 热度值, bvid)
                             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                    cursor.execute(sql, (
                        data["硬币数量"], data["播放量"], data["发布时间"], data["发布时长"],
                        data["弹幕量"], data["评论量"], data["收藏量"], data["分享数"],
                        data["点赞"], data["视频时长"], data["视频标题"], hot, data["bvid"]
                    ))
            connection.commit()
        finally:
            connection.close()

    def count_arc_hot(self, coin, fav, danmaku, reply, view, like, share, ptime):
        hot = coin * 0.4 + fav * 0.3 + danmaku * 0.4 + reply * 0.4 + view * 0.25 + like * 0.4 + share * 0.6
        current_time = datetime.now().timestamp()
        if ptime >= current_time - 86400:  # 如果是一天内发布的视频
            hot *= 1.5
        return math.floor(hot)

    def convert_to_days(self, time_str):
        days, hours, minutes = 0, 0, 0
        if "天" in time_str:
            parts = time_str.split("天")
            days = int(parts[0])
            remainder = parts[1] if len(parts) > 1 else ''
            if "小时" in remainder:
                parts = remainder.split("小时")
                hours = int(parts[0])
                remainder = parts[1] if len(parts) > 1 else ''
            if "分钟" in remainder:
                minutes = int(remainder.split("分钟")[0])
        return days + hours / 24 + minutes / 1440

    def convert_to_seconds(self, time_str):
        minutes, seconds = time_str.split("分")
        seconds = seconds.split("秒")[0]
        return int(minutes) * 60 + int(seconds)

    def fetch_video_details(self, bvid):
        url = f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}'
        ua = UserAgent()
        user_agents = [ua.ie, ua.opera, ua.chrome, ua.firefox, ua.safari]
        headers = {
            'User-Agent': random.choice(user_agents),
            'Cookie': 'your_cookie_here'
        }
        response = rq.get(url, headers=headers)
        data = json.loads(response.text)
        return data['data']['stat'], data['data']['ctime'], data['data']['duration'], data['data']['title']

    def predict_and_show(self, data_list):
        # 数据预处理
        for data in data_list:
            data["发布时长_天"] = self.convert_to_days(data["发布时长"])
            data["视频时长_秒"] = self.convert_to_seconds(data["视频时长"])

            hot = self.count_arc_hot(
                data["硬币数量"], data["收藏量"], data["弹幕量"],
                data["评论量"], data["播放量"], data["点赞"],
                data["分享数"], datetime.strptime(data["发布时间"], "%Y-%m-%d %H:%M:%S").timestamp()
            )
            data['热度值'] = hot
            print(data)

        df = pd.DataFrame(data_list)
        features = ["硬币数量", "弹幕量", "评论量", "收藏量", "分享数", "点赞", "发布时长_天", "视频时长_秒", "热度值"]
        try:
            X = df[features]
        except Exception as e:
            print(f"捕获到异常，为{e}")
            wx.MessageBox("直播间不可进行此操作", "Failure", wx.OK | wx.ICON_WARNING)


        # 使用训练好的模型进行预测
        y_pred = self.model.predict(X)
        df["预测播放量"] = y_pred

        # 可视化预测结果
        self.show_prediction_chart(df)

    def on_back(self, event):
        self.Close()
        self.parent.Show()

    def on_exit(self, event):
        self.Close()
        self.parent.Close()

    def InitUI(self):
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.combo_box = wx.ComboBox(panel, choices=self.df["视频标题"].tolist())
        self.combo_box.Bind(wx.EVT_COMBOBOX, self.on_combobox)
        sizer.Add(self.combo_box, 0, wx.ALL | wx.EXPAND, 5)
        panel.SetSizer(sizer)
        self.Centre()
        self.Show(True)

    def on_combobox(self, event):
        selected_title = self.combo_box.GetValue()
        selected_data = self.df[self.df["视频标题"] == selected_title]
        if not selected_data.empty:
            self.show_prediction_chart(selected_data)
        else:
            wx.MessageBox('无相关数据', '错误', wx.OK | wx.ICON_ERROR)

    def show_prediction_chart(self, df):
        # 检查数据类型
        print(df.dtypes)

        # 确保播放量数据是数值型
        df["播放量"] = pd.to_numeric(df["播放量"], errors='coerce')
        df["预测播放量"] = pd.to_numeric(df["预测播放量"], errors='coerce')

        # 检查是否有任何播放量数据为 NaN 并进行处理
        print(df.isna().sum())

        # 初始化 wx 应用
        app = wx.App(False)
        frame = wx.Frame(None, wx.ID_ANY, "预测结果", size=(1200, 800))  # 调整窗口大小
        panel = wx.Panel(frame, wx.ID_ANY)
        sizer = wx.BoxSizer(wx.VERTICAL)

        fig = Figure(figsize=(15, 8))  # 调整图表大小
        ax = fig.add_subplot(111)

        # 绘制实际播放量和预测播放量曲线
        ax.plot(df["视频标题"], df["播放量"], label='实际播放量', marker='o')
        ax.plot(df["视频标题"], df["预测播放量"], label='预测播放量', marker='x')

        # 设置 y 轴的刻度和范围
        ax.set_yscale('linear')  # 确保 y 轴使用线性比例

        # 限制标题为两个字
        short_titles = df["视频标题"].apply(lambda x: x[:3])
        ax.set_xticks(range(len(short_titles)))
        ax.set_xticklabels(short_titles, rotation=30, ha='right')

        ax.set_xlabel("视频标题")
        ax.set_ylabel("播放量")
        ax.set_title("视频播放量预测")
        ax.legend()

        # 添加 mplcursors 以在鼠标悬停时显示标题
        cursor = mplcursors.cursor(ax, hover=True)

        @cursor.connect("add")
        def on_add(sel):
            index = int(sel.index)  # 转换索引为整数
            play_count = df["播放量"].iloc[index]
            pred_count = df["预测播放量"].iloc[index]
            sel.annotation.set_text(f"实际: {play_count}\n预测: {pred_count}")
            sel.annotation.xy = (sel.target[0], sel.target[1])
            sel.annotation.xytext = (10, 10)
            sel.annotation.textcoords = 'offset points'

        canvas = FigureCanvas(panel, -1, fig)
        sizer.Add(canvas, 1, wx.EXPAND | wx.ALL, 10)

        panel.SetSizer(sizer)
        frame.Show()
        app.MainLoop()

# 比较
class ComparisonFrame(wx.Frame):

    def __init__(self, parent, data_list):
        super(ComparisonFrame, self).__init__(parent)
        self.parent = parent
        self.data_list = data_list

        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(wx.Colour(255, 255, 255))  # 设置背景颜色为白色

        self.title = wx.StaticText(self.panel, label="选择视频进行热度比较", style=wx.ALIGN_CENTER)
        title_font = wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.title.SetFont(title_font)

        label_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        self.check_list = wx.CheckListBox(self.panel, size=(300, 200), choices=[item['标题'] for item in data_list])
        self.check_list.SetFont(label_font)

        button_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        back_button = wx.Button(self.panel, label="返回", size=(150, 50))
        back_button.SetFont(button_font)
        exit_button = wx.Button(self.panel, label="退出", size=(150, 50))
        exit_button.SetFont(button_font)
        select_all_button = wx.Button(self.panel, label="全部勾选", size=(250, 50))
        select_all_button.SetFont(button_font)
        start_comparison_button = wx.Button(self.panel, label="开始比较", size=(250, 50))
        start_comparison_button.SetFont(button_font)

        back_button.Bind(wx.EVT_BUTTON, self.on_back)
        exit_button.Bind(wx.EVT_BUTTON, self.on_exit)
        select_all_button.Bind(wx.EVT_BUTTON, self.on_select_all)
        start_comparison_button.Bind(wx.EVT_BUTTON, self.on_start_comparison)

        # 布局
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.title, 0, wx.ALIGN_CENTER | wx.ALL, 20)
        sizer.Add(self.check_list, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(back_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        button_sizer.Add(exit_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        sizer.Add(select_all_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.Add(start_comparison_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        self.panel.SetSizer(sizer)

        self.SetTitle("Bilibili视频平台数据获取及预测系统V1.0")
        self.SetSize((500, 700))

        MainFrame.xy(self)

    def on_select_all(self, event):
        for i in range(len(self.data_list)):
            self.check_list.Check(i)

    def on_start_comparison(self, event):
        selected_indices = self.check_list.GetCheckedItems()
        if selected_indices:
            selected_items = [self.data_list[i] for i in selected_indices]
            self.show_comparison_chart(selected_items)
        else:
            wx.MessageBox("请选择一个或多个视频进行比较", "提示", wx.OK | wx.ICON_INFORMATION)

    def on_back(self, event):
        self.Close()
        self.parent.Show()

    def on_exit(self, event):
        self.Close()

    def show_comparison_chart(self, data_list):
        app = wx.App(False)
        frame = wx.Frame(None, wx.ID_ANY, "比较结果", size=(1000, 700))
        panel = wx.ScrolledWindow(frame, wx.ID_ANY)
        panel.SetScrollRate(20, 20)

        sizer = wx.BoxSizer(wx.VERTICAL)

        # Function to create and add a chart
        def add_chart(titles, counts, label, color):
            fig = Figure(figsize=(10, 4))
            ax = fig.add_subplot(111)
            ax.plot(titles, counts, label=label, marker='o', linestyle='-', color=color)
            ax.set_xlabel("视频标题")
            ax.set_ylabel("数量")
            ax.set_title(f"{label} 比较")
            ax.legend()
            ax.set_xticks(np.arange(len(titles)))
            ax.set_xticklabels(titles, rotation=45, ha='right')

            cursor = mplcursors.cursor(ax, hover=True)

            @cursor.connect("add")
            def on_add(sel):
                index = int(sel.index)
                title = titles[index]
                count = counts[index]
                sel.annotation.set(
                    text=f"{title}\n{label}: {count}"
                )

            # 标记0或空数据
            for i, count in enumerate(counts):
                if count == 0:
                    ax.annotate('0数据(直播间)', (i, count), textcoords="offset points", xytext=(0, 10), ha='center',
                                color='red')
                elif count is None:
                    ax.annotate('空数据(直播间)', (i, 0), textcoords="offset points", xytext=(0, 10), ha='center',
                                color='red')

            canvas = FigureCanvas(panel, -1, fig)
            sizer.Add(canvas, 0, wx.EXPAND | wx.ALL, 10)

        # Limit titles to two characters and ensure uniqueness
        titles = [item['标题'][:3] for item in data_list]
        unique_titles = [f"{title}_{i}" for i, title in enumerate(titles)]

        # Convert video length to seconds for comparison
        def time_to_seconds(time_str):
            if not time_str:
                return 0
            parts = list(map(int, time_str.split(':')))
            if len(parts) == 3:
                h, m, s = parts
            elif len(parts) == 2:
                h = 0
                m, s = parts
            else:
                h = 0
                m = 0
                s = parts[0]
            return h * 3600 + m * 60 + s

        def format_time(seconds):
            h = seconds // 3600
            m = (seconds % 3600) // 60
            s = seconds % 60
            return f'{h}:{m:02d}:{s:02d}'

        # Extract and align data
        real_counts = []
        length_counts = []
        like_counts = []
        danmaku_counts = []
        comment_counts = []
        favorite_counts = []

        for item in data_list:
            real_counts.append(item['播放量'] if item['播放量'] is not None else 0)
            length_counts.append(time_to_seconds(item['视频时长']) if item['视频时长'] is not None else 0)
            like_counts.append(item['点赞数'] if item['点赞数'] is not None else 0)
            danmaku_counts.append(item['弹幕数'] if item['弹幕数'] is not None else 0)
            comment_counts.append(item['评论数'] if item['评论数'] is not None else 0)
            favorite_counts.append(item['收藏数'] if item['收藏数'] is not None else 0)

        # Add individual charts
        add_chart(unique_titles, real_counts, '实际播放量', 'b')
        add_chart(unique_titles, length_counts, '视频时长', 'g')
        add_chart(unique_titles, like_counts, '点赞数', 'r')
        add_chart(unique_titles, danmaku_counts, '弹幕数', 'm')
        add_chart(unique_titles, comment_counts, '评论数', 'c')
        add_chart(unique_titles, favorite_counts, '收藏数', 'y')

        panel.SetSizer(sizer)
        panel.FitInside()  # Ensure the panel fits inside the scrolled window
        frame.Show()
        app.MainLoop()


if __name__ == '__main__':
    app = wx.App(False)
    login_frame = MainFrame(None)
    login_frame.Show(True)
    app.MainLoop()





