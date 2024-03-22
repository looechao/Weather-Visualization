import requests
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import numpy as np
import seaborn as sns
import io
import base64
import squarify
from scipy.stats import spearmanr
from scipy.stats import pearsonr
from pylab import mpl

mpl.rcParams['font.sans-serif'] = ['SimHei']
mpl.rcParams['axes.unicode_minus'] = False

# 设置API Key和城市名称
key = "RMQAQKSKXNZTTST4DTTEVD6XX"
city = "changsha"

#获取今天的日期和30天的日期：
today = datetime.date.today()
start_date = today - datetime.timedelta(days=29)
print(today,start_date)

# 定义变量：是否需要更新数据，默认为True
update_data = True

## 判断用户是否需要更新数据，如果不需要，则从本地加载历史缓存数据
if not update_data:
    try:
        with open("weather_data.json", "r", encoding="utf-8") as f:
            jsonData = json.load(f)
    except FileNotFoundError:
        print("无法找到历史缓存数据文件，请设置update_data=True以更新数据")
        exit()
else:
    ### 发送API请求获取数据
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}/{start_date}/{today}"
    querystring = {"unitGroup":"metric","include":"days","key":"RMQAQKSKXNZTTST4DTTEVD6XX","contentType":"json"}
    response = requests.request("GET", url, params=querystring)

    ### 检测响应结果，若响应成功（status_code=200）,则返回数据，反之则返回HTTP错误代码
    if response.status_code == 200:
        ####将文本解析成json数据
        jsonData = json.loads(response.text)

        ####保存API返回的数据为历史缓存
        with open("weather_data.json", "w", encoding="utf-8") as f:
            json.dump(jsonData, f, ensure_ascii=False)
    else:
        print(f"HTTP error {response.status_code}")
        exit()

#将json转换成dataframe结构：
df = pd.json_normalize(jsonData['days'],meta=['datetime'])
df.info()

#绘制折线图
##将tempmax、tempmin、temp列提取出来
temp_max = df['tempmax']
temp_min = df['tempmin']
temp_avg = df['temp']

##将datetime作为x轴
x_axis = df['datetime']
x_axis = [mdates.datestr2num(date) for date in x_axis]

##绘制三条折线，分别表示最高温度、最低温度和平均温度
fig1=plt.figure()
plt.plot(x_axis, temp_max, label='最高气温',color='red')
plt.plot(x_axis, temp_min, label='最低气温',color='green')
plt.plot(x_axis, temp_avg, label='平均气温',color='blue')

##添加图例
plt.legend()

##设置x轴和y轴标签
plt.xlabel('日期（天）')
plt.ylabel('温度 (°C)')

##设置横坐标刻度的格式
date_format = mdates.DateFormatter('%d') # 只显示日期的日部分
ax = plt.gca()
ax.xaxis.set_major_formatter(date_format)

#添加阴影：
plt.fill_between(x_axis, df['tempmax'], df['tempmin'], color='#AFEEEE', alpha=0.2)


##设置第一个窗口的标题
fig1.suptitle('过去30天长沙市气温变化')




#绘制天气占比图
##统计各天气类型的记录数counts,并生成新的DF
conditions_counts=df['conditions'].value_counts().reset_index()
conditions_counts.columns=['conditions','count']
print(conditions_counts)
#将列元素提取出来
count=conditions_counts['count']
conditions=conditions_counts['conditions']
colors = ['#87CEFA', '#A9A9A9', '#6495ED', '#808080','#FFFF00']
##绘制饼图
fig2=plt.figure(num=2)
plt.pie(count,labels=conditions,colors=colors)

##添加图例
plt.legend(conditions,loc='best',fontsize=7)

#设置标题
fig2.suptitle('不同天气类型的占比')

'''
#分析月相与天气状态的关系：
##将icon列转换为数字编码
df['conditions_code']=pd.Categorical(df['conditions']).codes
print(df['conditions_code'])
#计算斯皮尔曼等级相关系数和P值
corr,p_value=spearmanr(df[['moonphase','conditions']])
print(f'Spearman rank correlation coefficient: {corr}\nP-value: {p_value}')
fig3=plt.figure(num=3)
sns.regplot(x='moonphase',y='conditions_code',data=df)

# 添加斯皮尔曼等级相关系数和 p 值到图表上
plt.annotate(f"Spearman's correlation={corr:.3f}\np-value={p_value:.3f}", 
             xy=(0.05, 0.85), xycoords='axes fraction')
'''

#分析月相与平均气温的关系：
##计算person相关系数和P值
corr, p_value = pearsonr(df['moonphase'], df['temp'])
print(f'皮尔逊相关系数为: {corr}\nP-value: {p_value}')
fig3=plt.figure(num=3)
sns.regplot(x='moonphase',y='temp',data=df)

##添加pearson相关系数和 p 值到图表上
plt.annotate(f"pearsonr={corr:.3f}\np_value={p_value:.3f}", 
             xy=(0.05, 0.85), xycoords='axes fraction')
##设置标题
fig3.suptitle('月相与平均气温的关系')



# 绘制日出和日落时间的折线图
fig4=plt.figure(num=4)

## 转换时间格式
df['sunrise'] = pd.to_datetime(df['sunrise'],errors='coerce')
df['sunset'] = pd.to_datetime(df['sunset'],errors='coerce')

## 按日期排序数据框
df_sorted = df.sort_values(by='datetime')

## 将日期转换为 matplotlib 可识别的格式
x_axis = pd.to_datetime(df_sorted['datetime']).apply(mdates.date2num)

## 绘制两条折线，分别表示日出时间和日落时间
plt.plot(x_axis, df_sorted['sunrise'], label='日出时间', color='yellow')
plt.plot(x_axis, df_sorted['sunset'], label='日落时间', color='red')

## 添加图例
plt.legend()

## 设置横坐标和纵坐标标签
plt.xlabel('日期（天）')
plt.ylabel('时间 (h)')

## 设置横坐标刻度的格式
date_format = mdates.DateFormatter('%d') # 只显示日期的日部分
ax = plt.gca()
ax.xaxis.set_major_formatter(date_format)

## 设置纵坐标刻度的格式
time_format = mdates.DateFormatter('%H:%M') # 设置时间的显示格式
ax.yaxis.set_major_formatter(time_format)  # 应用设置好的时间格式到纵坐标

## 设置窗口的标题
fig4.suptitle('日出和日落时间变化')


## 设置横坐标范围
plt.xlim(x_axis.min(), x_axis.max())
## 绘制两条折线之间的点阴影
plt.fill_between(x_axis, df_sorted['sunrise'], df['sunset'], color='#FFB6C1', alpha=0.2)



# 绘制云层覆盖率和降水量的关系
fig5=plt.figure(num=5)
cloudcover = df['cloudcover']
precip=df['precip']

# 绘制每个数据点的散点
ax = fig5.subplots()
ax.scatter(range(len(cloudcover)), cloudcover, label='云层覆盖率', color='blue')
ax.scatter(range(len(precip)), precip, label='降水量', color='green')

# 绘制折线，连接每个数据点
ax.plot(range(len(cloudcover)), cloudcover, linestyle='-', color='blue')
ax.plot(range(len(precip)), precip, linestyle='-', color='green')

# 添加图例、标签等
ax.set_xlabel('Day')
ax.set_ylabel('Value')
ax.legend()


# 将precip向上取整为整数，并转换为NumPy数组形式
precips = df['precip']
precips_int = np.ceil(precips).astype(int).values

# 将precips_int转换为二维数组形式
arr = precips_int.reshape(5,6)
labels = ['Day {}'.format(i+1) for i in range(len(precips))]

# 创建Figure对象和Axes对象，并显示矩形网格
fig, ax = plt.subplots()
im = ax.imshow(arr, cmap='Blues')

# 显示每个格子的标签
for i in range(arr.shape[0]):
    for j in range(arr.shape[1]):
        text = ax.text(j, i, labels[i*arr.shape[1]+j],
                       ha="center", va="center", color="w")

# 设置图表标题和坐标轴标签
ax.set_title('最近30天降水量', fontsize=18)
ax.set_xlabel('Day')
ax.set_ylabel('Week')

# 添加颜色条
cbar = ax.figure.colorbar(im, ax=ax, cmap='Blues')
cbar.ax.set_ylabel('Precipitation', rotation=-90, va="bottom")


plt.show()