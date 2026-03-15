# import pandas as pd
# import pymysql
# import joblib
# from sklearn.linear_model import LinearRegression
# from sklearn.model_selection import train_test_split
# from sklearn.metrics import mean_squared_error
#
#
# import re
# from datetime import datetime
# import joblib
# import matplotlib.pyplot as plt
#
# from pylab import mpl
# # 设置显示中文字体
# mpl.rcParams["font.sans-serif"] = ["SimHei"]
#
# def fetch_data():
#     conn = pymysql.connect(host='localhost',
#                            port=3306,
#                            user='root',
#                            password='1234567',
#                            db='world',
#                            charset='utf8mb4')
#     query = "SELECT * FROM video_details"
#     df = pd.read_sql(query, conn)
#     conn.close()
#     return df
#
# def train_model():
#     df = fetch_data()
#
#     def convert_to_days(duration):
#         days, hours, minutes = 0, 0, 0
#         if "天" in duration:
#             parts = duration.split(" 天 ")
#             days = int(parts[0])
#             remainder = parts[1]
#             if "小时" in remainder:
#                 parts = remainder.split(" 小时 ")
#                 hours = int(parts[0])
#                 remainder = parts[1]
#             if "分钟" in remainder:
#                 minutes = int(remainder.split(" 分钟")[0])
#         return days + hours / 24 + minutes / 1440
#
#     df["发布时长_天"] = df["发布时长"].apply(convert_to_days)
#
#     def convert_to_seconds(duration):
#         minutes, seconds = duration.split(" 分 ")
#         seconds = seconds.split(" 秒")[0]
#         return int(minutes) * 60 + int(seconds)
#
#     df["视频时长_秒"] = df["视频时长"].apply(convert_to_seconds)
#     df["发布时间"] = pd.to_datetime(df["发布时间"])
#
#     features = ["硬币数量", "弹幕量", "评论量", "收藏量", "分享数", "点赞", "发布时长_天", "视频时长_秒", "播放量"]
#     target = "热度值"
#
#     X = df[features]
#     y = df[target]
#
#     X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
#
#     model = LinearRegression()
#     model.fit(X_train, y_train)
#
#     y_pred = model.predict(X_test)
#     mse = mean_squared_error(y_test, y_pred)
#     print(f"模型均方误差: {mse}")
#
#     # joblib.dump(model, "linear_regression_model.pkl")
#     joblib.dump(model, "video_popularity_model.pkl")
#
#     plt.figure(figsize=(10, 6))
#     plt.scatter(y_test, y_pred, alpha=0.6)
#     plt.xlabel("实际播放量")
#     plt.ylabel("预测播放量")
#     plt.title("播放量预测对比")
#     plt.show()
#
# if __name__ == "__main__":
#     train_model()

# ==============================================================================================


#
# # 定义将发布时长转换为天数的函数
# def convert_to_days(duration):
#     days, hours, minutes = 0, 0, 0
#     if "天" in duration:
#         parts = duration.split(" 天 ")
#         days = int(parts[0])
#         remainder = parts[1]
#         if "小时" in remainder:
#             parts = remainder.split(" 小时 ")
#             hours = int(parts[0])
#             remainder = parts[1]
#         if "分钟" in remainder:
#             minutes = int(remainder.split(" 分钟")[0])
#     return days + hours / 24 + minutes / 1440
#
# # 定义将视频时长转换为秒数的函数
# def convert_to_seconds(duration):
#     minutes, seconds = duration.split(" 分 ")
#     seconds = seconds.split(" 秒")[0]
#     return int(minutes) * 60 + int(seconds)
#
# # 从数据库获取数据
# def fetch_data():
#     conn = pymysql.connect(host='localhost',
#                            port=3306,
#                            user='root',
#                            password='1234567',
#                            db='world',
#                            charset='utf8mb4')
#     query = "SELECT * FROM video_details"
#     df = pd.read_sql(query, conn)
#     conn.close()
#     return df
#
# # 获取数据并进行预处理
# df = fetch_data()
# df["发布时长_天"] = df["发布时长"].apply(convert_to_days)
# df["视频时长_秒"] = df["视频时长"].apply(convert_to_seconds)
#
# # 选择用于训练的特征
# features = ["硬币数量", "弹幕量", "评论量", "收藏量", "分享数", "点赞", "发布时长_天", "视频时长_秒"]
# X = df[features]
# y = df["播放量"]
#
# # 划分训练集和测试集
# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
#
# # 训练回归模型
# regressor = LinearRegression()
# regressor.fit(X_train, y_train)
#
# # 在测试集上进行预测
# y_pred = regressor.predict(X_test)
#
# # 评估模型性能
# mse = mean_squared_error(y_test, y_pred)
# print(f"均方误差: {mse}")
#
# # 保存模型
# joblib.dump(regressor, "video_popularity_model.pkl")
#
# # 可视化结果

import pandas as pd
import pymysql
import joblib
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error


import re
from datetime import datetime
import joblib
import matplotlib.pyplot as plt

from pylab import mpl
# 设置显示中文字体
mpl.rcParams["font.sans-serif"] = ["SimHei"]
'''
def fetch_data():
    conn = pymysql.connect(host='localhost',
                           port=3306,
                           user='root',
                           password='1234567',
                           db='world',
                           charset='utf8mb4')
    query = "SELECT * FROM video_details"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def train_model():
    df = fetch_data()
    print(df)

    def convert_to_days(duration):
        days, hours, minutes = 0, 0, 0
        if "天" in duration:
            parts = duration.split(" 天 ")
            days = int(parts[0])
            remainder = parts[1]
            if "小时" in remainder:
                parts = remainder.split(" 小时 ")
                hours = int(parts[0])
                remainder = parts[1]
            if "分钟" in remainder:
                minutes = int(remainder.split(" 分钟")[0])
        return days + hours / 24 + minutes / 1440

    df["发布时长_天"] = df["发布时长"].apply(convert_to_days)

    def convert_to_seconds(duration):
        minutes, seconds = duration.split(" 分 ")
        seconds = seconds.split(" 秒")[0]
        return int(minutes) * 60 + int(seconds)

    df["视频时长_秒"] = df["视频时长"].apply(convert_to_seconds)
    df["发布时间"] = pd.to_datetime(df["发布时间"])

    features = ["硬币数量", "弹幕量", "评论量", "收藏量", "分享数", "点赞", "发布时长_天", "视频时长_秒", "热度值"]
    target = "播放量"

    X = df[features]
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    print(f"模型均方误差: {mse}")

    # joblib.dump(model, "video_popularity_model.pkl")

    plt.figure(figsize=(10, 6))
    plt.scatter(y_test, y_pred, alpha=0.6)
    plt.xlabel("实际播放量")
    plt.ylabel("预测播放量")
    plt.title("播放量预测对比")
    plt.show()

if __name__ == "__main__":
    train_model()
'''

# import pandas as pd
# import pymysql
# from sklearn.linear_model import Ridge
# from sklearn.model_selection import train_test_split, cross_val_score
# from sklearn.metrics import mean_squared_error
# import matplotlib.pyplot as plt
#
# def fetch_data():
#     conn = pymysql.connect(host='localhost',
#                            port=3306,
#                            user='root',
#                            password='1234567',
#                            db='world',
#                            charset='utf8mb4')
#     query = "SELECT * FROM video_details"
#     df = pd.read_sql(query, conn)
#     conn.close()
#     return df
#
# def train_model():
#     df = fetch_data()
#     print(df)
#
#     def convert_to_days(duration):
#         days, hours, minutes = 0, 0, 0
#         if "天" in duration:
#             parts = duration.split("天")
#             days = int(parts[0])
#             remainder = parts[1] if len(parts) > 1 else ''
#             if "小时" in remainder:
#                 parts = remainder.split("小时")
#                 hours = int(parts[0])
#                 remainder = parts[1] if len(parts) > 1 else ''
#             if "分钟" in remainder:
#                 minutes = int(remainder.split("分钟")[0])
#         return days + hours / 24 + minutes / 1440
#
#     def convert_to_seconds(duration):
#         minutes, seconds = duration.split("分")
#         seconds = seconds.split("秒")[0]
#         return int(minutes) * 60 + int(seconds)
#
#     df["发布时长_天"] = df["发布时长"].apply(convert_to_days)
#     df["视频时长_秒"] = df["视频时长"].apply(convert_to_seconds)
#     df["发布时间"] = pd.to_datetime(df["发布时间"])
#
#     features = ["硬币数量", "弹幕量", "评论量", "收藏量", "分享数", "点赞", "发布时长_天", "视频时长_秒", "热度值"]
#     target = "播放量"
#
#     X = df[features]
#     y = df[target]
#
#     X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
#
#     model = Ridge(alpha=1.0)  # 使用岭回归，alpha为正则化参数
#     model.fit(X_train, y_train)
#
#     y_pred = model.predict(X_test)
#     mse = mean_squared_error(y_test, y_pred)
#     print(f"模型均方误差: {mse}")
#
#     # 使用交叉验证评估模型
#     scores = cross_val_score(model, X, y, cv=5, scoring='neg_mean_squared_error')
#     avg_mse = -scores.mean()
#     print(f"交叉验证平均均方误差: {avg_mse}")
#
#     plt.figure(figsize=(10, 6))
#     plt.scatter(y_test, y_pred, alpha=0.6)
#     plt.xlabel("实际播放量")
#     plt.ylabel("预测播放量")
#     plt.title("播放量预测对比")
#     plt.show()
#
# if __name__ == "__main__":
#     train_model()


# import pandas as pd
# import pymysql
# from sklearn.linear_model import Ridge
# from sklearn.model_selection import train_test_split, cross_val_score
# from sklearn.metrics import mean_squared_error
# import matplotlib.pyplot as plt
#
#
# def fetch_data():
#     conn = pymysql.connect(host='localhost',
#                            port=3306,
#                            user='root',
#                            password='1234567',
#                            db='world',
#                            charset='utf8mb4')
#     query = "SELECT * FROM video_details"
#     df = pd.read_sql(query, conn)
#     conn.close()
#     return df
#
#
# def train_model():
#     df = fetch_data()
#     print(df)
#
#     def convert_to_days(duration):
#         days, hours, minutes = 0, 0, 0
#         if "天" in duration:
#             parts = duration.split("天")
#             days = int(parts[0])
#             remainder = parts[1] if len(parts) > 1 else ''
#             if "小时" in remainder:
#                 parts = remainder.split("小时")
#                 hours = int(parts[0])
#                 remainder = parts[1] if len(parts) > 1 else ''
#             if "分钟" in remainder:
#                 minutes = int(remainder.split("分钟")[0])
#         return days + hours / 24 + minutes / 1440
#
#     def convert_to_seconds(duration):
#         minutes, seconds = duration.split("分")
#         seconds = seconds.split("秒")[0]
#         return int(minutes) * 60 + int(seconds)
#
#     df["发布时长_天"] = df["发布时长"].apply(convert_to_days)
#     df["视频时长_秒"] = df["视频时长"].apply(convert_to_seconds)
#     df["发布时间"] = pd.to_datetime(df["发布时间"])
#
#     features = ["硬币数量", "弹幕量", "评论量", "收藏量", "分享数", "点赞", "发布时长_天", "视频时长_秒", "热度值"]
#     target = "播放量"
#
#     X = df[features]
#     y = df[target]
#
#     X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
#
#     model = Ridge(alpha=1.0)
#     model.fit(X_train, y_train)
#
#     y_pred = model.predict(X_test)
#     mse = mean_squared_error(y_test, y_pred)
#     print(f"模型均方误差: {mse}")
#
#     # 使用交叉验证评估模型
#     scores = cross_val_score(model, X, y, cv=5, scoring='neg_mean_squared_error')
#     avg_mse = -scores.mean()
#     print(f"交叉验证平均均方误差: {avg_mse}")
#
#     # 打印实际值和预测值的对比表格
#     comparison = pd.DataFrame({"实际播放量": y_test, "预测播放量": y_pred})
#     print(comparison.head(10))  # 打印前10行对比
#
#     plt.figure(figsize=(10, 6))
#     plt.scatter(y_test, y_pred, alpha=0.6)
#     plt.xlabel("实际播放量")
#     plt.ylabel("预测播放量")
#     plt.title("播放量预测对比")
#
#     # 调整坐标轴范围，确保显示实际数据范围
#     plt.xlim(min(y_test.min(), y_pred.min()) * 0.9, max(y_test.max(), y_pred.max()) * 1.1)
#     plt.ylim(min(y_test.min(), y_pred.min()) * 0.9, max(y_test.max(), y_pred.max()) * 1.1)
#
#     plt.show()
#
# if __name__ == "__main__":
#     train_model()















# import pandas as pd
# import pymysql
# from sklearn.linear_model import Ridge
# from sklearn.model_selection import train_test_split, cross_val_score
# from sklearn.metrics import mean_squared_error
# import matplotlib.pyplot as plt
#
#
# def fetch_data():
#     conn = pymysql.connect(host='localhost',
#                            port=3306,
#                            user='root',
#                            password='1234567',
#                            db='world',
#                            charset='utf8mb4')
#     query = "SELECT * FROM video_details"
#     df = pd.read_sql(query, conn)
#     conn.close()
#     return df
#
#
# def convert_to_days(duration):
#     days, hours, minutes = 0, 0, 0
#     if "天" in duration:
#         parts = duration.split("天")
#         days = int(parts[0])
#         remainder = parts[1] if len(parts) > 1 else ''
#         if "小时" in remainder:
#             parts = remainder.split("小时")
#             hours = int(parts[0])
#             remainder = parts[1] if len(parts) > 1 else ''
#         if "分钟" in remainder:
#             minutes = int(remainder.split("分钟")[0])
#     return days + hours / 24 + minutes / 1440
#
#
# def convert_to_seconds(duration):
#     minutes, seconds = duration.split("分")
#     seconds = seconds.split("秒")[0]
#     return int(minutes) * 60 + int(seconds)
#
#
# def train_model():
#     df = fetch_data()
#
#     # 数据转换
#     df["发布时长_天"] = df["发布时长"].apply(convert_to_days)
#     df["视频时长_秒"] = df["视频时长"].apply(convert_to_seconds)
#     df["发布时间"] = pd.to_datetime(df["发布时间"])
#
#     # 特征和目标变量
#     features = ["硬币数量", "弹幕量", "评论量", "收藏量", "分享数", "点赞", "发布时长_天", "视频时长_秒", "热度值"]
#     target = "播放量"
#
#     X = df[features]
#     y = df[target]
#
#     # 数据分割
#     X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
#
#     # 使用 Ridge 回归模型
#     model = Ridge(alpha=1.0)
#     model.fit(X_train, y_train)
#
#     y_pred = model.predict(X_test)
#     mse = mean_squared_error(y_test, y_pred)
#     print(f"模型均方误差: {mse}")
#
#     # 使用交叉验证评估模型
#     scores = cross_val_score(model, X, y, cv=5, scoring='neg_mean_squared_error')
#     avg_mse = -scores.mean()
#     print(f"交叉验证平均均方误差: {avg_mse}")
#
#     # 打印实际值和预测值的对比表格
#     comparison = pd.DataFrame({"实际播放量": y_test, "预测播放量": y_pred})
#     print(comparison.head(10))
#
#     # 生成散点图
#     plt.figure(figsize=(10, 6))
#     plt.scatter(y_test, y_pred, alpha=0.6)
#     plt.xlabel("实际播放量")
#     plt.ylabel("预测播放量")
#     plt.title("播放量预测对比")
#
#     # 调整坐标轴范围，确保显示实际数据范围
#     plt.xlim(0, y_test.max() * 0.001)
#     plt.ylim(0, y_pred.max() * 0.001)
#
#     plt.show()
#
#
# if __name__ == "__main__":
#     train_model()










import pandas as pd
import pymysql
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt
import numpy as np

def fetch_data():
    conn = pymysql.connect(host='localhost',
                           port=3306,
                           user='root',
                           password='1234567',
                           db='world',
                           charset='utf8mb4')
    query = "SELECT * FROM video_details"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def convert_to_days(duration):
    days, hours, minutes = 0, 0, 0
    if "天" in duration:
        parts = duration.split("天")
        days = int(parts[0])
        remainder = parts[1] if len(parts) > 1 else ''
        if "小时" in remainder:
            parts = remainder.split("小时")
            hours = int(parts[0])
            remainder = parts[1] if len(parts) > 1 else ''
        if "分钟" in remainder:
            minutes = int(remainder.split("分钟")[0])
    return days + hours / 24 + minutes / 1440

def convert_to_seconds(duration):
    minutes, seconds = duration.split("分")
    seconds = seconds.split("秒")[0]
    return int(minutes) * 60 + int(seconds)

def train_model():
    df = fetch_data()
    print(df)
    # 数据转换
    df["发布时长_天"] = df["发布时长"].apply(convert_to_days)
    df["视频时长_秒"] = df["视频时长"].apply(convert_to_seconds)
    df["发布时间"] = pd.to_datetime(df["发布时间"])

    # 特征和目标变量
    features = ["硬币数量", "弹幕量", "评论量", "收藏量", "分享数", "点赞", "发布时长_天", "视频时长_秒", "热度值"]
    target = "播放量"

    # 排除播放量为0的样本
    df = df[df[target] > 0]

    X = df[features]
    y = df[target]

    # 数据分割
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 使用 Ridge 回归模型
    model = Ridge(alpha=1.0)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_pred = np.maximum(0, y_pred)  # 确保预测值为非负数

    mse = mean_squared_error(y_test, y_pred)
    print(f"模型均方误差: {mse}")

    # 使用交叉验证评估模型
    scores = cross_val_score(model, X, y, cv=5, scoring='neg_mean_squared_error')
    avg_mse = -scores.mean()
    print(f"交叉验证平均均方误差: {avg_mse}")

    # 打印实际值和预测值的对比表格
    comparison = pd.DataFrame({"实际播放量": y_test, "预测播放量": y_pred})
    print(comparison.head(10))

    # 生成散点图
    plt.figure(figsize=(10, 6))
    plt.scatter(y_test, y_pred, alpha=0.6)
    plt.xlabel("实际播放量")
    plt.ylabel("预测播放量")
    plt.title("播放量预测对比")

    # 调整坐标轴范围，确保显示实际数据范围
    plt.xlim(0, y_test.max() * 0.09)
    plt.ylim(0, y_pred.max() * 0.09)

    plt.show()
    joblib.dump(model, "video_popularity_model.pkl")

if __name__ == "__main__":
    train_model()








