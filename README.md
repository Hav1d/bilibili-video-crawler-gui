<video src="https://private-user-images.githubusercontent.com/194333139/563695408-5cb0472f-3608-419c-9709-3aae16bb8524.mp4?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NzM1Njk1MzYsIm5iZiI6MTc3MzU2OTIzNiwicGF0aCI6Ii8xOTQzMzMxMzkvNTYzNjk1NDA4LTVjYjA0NzJmLTM2MDgtNDE5Yy05NzA5LTNhYWUxNmJiODUyNC5tcDQ_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjYwMzE1JTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI2MDMxNVQxMDA3MTZaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT1jMTAwNmM0ODk3OWVmMmRlYmVlMThhM2EzOGRhODEzZTA0NzQ0ZmZlNDBmMGE4M2IwOTQzZTMzZGE3MDdmOTkzJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.Iuh9mvC8EartuAViQLwq3Kv_y13kgv92KxE4w693S_A" controls="controls" width="100%"></video>

# 📺 Bilibili 视频数据获取与热度预测系统 (Bilibili Data Analyzer & Predictor)

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![MySQL](https://img.shields.io/badge/MySQL-Supported-orange.svg)
![Machine Learning](https://img.shields.io/badge/Machine%20Learning-Scikit--Learn-yellow.svg)
![GUI](https://img.shields.io/badge/GUI-wxPython-lightgrey.svg)


## 📖 项目简介

本项目是一个基于 Python 开发的 Bilibili 视频平台数据获取、可视化分析及热度预测的综合性桌面端软件。
系统通过绕过 Bilibili 反爬机制获取视频详细数据，利用异步多线程技术高效下载封面并存入 MySQL 数据库。同时，内置了基于机器学习（岭回归/梯度提升树）的预测模型，能够根据视频的各项历史指标对未来的播放量和热度进行科学预测。

## ✨ 核心功能

* **🔐 权限与账户管理**：支持普通用户与管理员双角色登录。管理员可查看系统日志（登录、搜索、预测日志）并管理用户账户。
* **🕷️ 智能数据爬取**：
    * 输入关键词和页数，自动调用 Bilibili API 接口抓取视频信息。
    * 突破 Bilibili 图片防盗链限制，采用 `asyncio` + `aiohttp` 异步多线程技术高速下载封面展示。
* **📊 多维度数据分析与排序**：支持对搜索结果按照“视频时长”、“点赞数”、“收藏数”、“弹幕数”、“评论数”及“播放量”进行动态排序。
* **📈 机器学习热度预测**：
    * 提取硬币、弹幕、评论、收藏、分享等特征。
    * 使用 `Scikit-Learn` 训练回归模型，预测视频未来的播放量，并直观输出拟合折线图。
* **📉 数据可视化对比**：勾选多个视频，使用 `Matplotlib` 自动生成柱状图/折线图，直观对比各项互动数据。

## 🛠️ 技术栈

* **开发语言**：Python
* **图形界面 (GUI)**：`wxPython`
* **数据库**：MySQL, `pymysql`, `sqlalchemy`
* **网络爬虫**：`requests`, `aiohttp`, `asyncio`, `fake_useragent`
* **数据处理**：`pandas`, `numpy`
* **机器学习**：`scikit-learn` (Ridge Regression, Gradient Boosting), `joblib`
* **数据可视化**：`matplotlib`

## ⚙️ 快速开始

### 1. 环境依赖
请确保你的电脑已安装 Python 3.8 或以上版本，并在命令行运行以下命令安装所需依赖库：
```bash
pip install wxPython pymysql sqlalchemy requests aiohttp aiofiles fake_useragent pandas numpy scikit-learn matplotlib joblib pillow
```
### 2. 数据库配置
确保本地已安装并启动 MySQL 服务 (默认端口 3306)。

创建名为 world 的数据库。

依次导入项目 database 文件夹中的 SQL 文件以初始化表结构和默认数据：

root.sql / super_root.sql / user.sql / video_details.sql

若你的数据库密码不是默认密码，请在 main.py 和 Generate_model.py 中修改 pymysql.connect 的 password 字段。

### 3. 运行程序
环境配置完成后，在项目根目录运行主程序：

```bash
python main.py
```
(注：如果需要重新训练机器学习模型，可以运行 python Generate_model.py)

## 📸 界面预览

* **登录与主界面**

* **数据搜索与排序**

* **热度对比与模型预测**

* **后台管理员日志**

## 🤝 贡献与许可
本项目为Hav1d个人独立开发，仅供学习和学术交流使用，请勿用于商业用途或恶意爬取 Bilibili 服务器，谢谢！
