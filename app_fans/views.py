from django.http import JsonResponse
from django.shortcuts import render
import re
import os
import pandas as pd
from datetime import datetime, timedelta


def filter_df_via_content(df:pd.DataFrame, query_keywords, cond, cate, weeks)->pd.DataFrame:

    # end date: the date of the latest record of news
    end_date = df['timestamp'].max()
    
    # start date
    start_date_delta = (datetime.strptime(end_date, '%Y-%m-%d').date() - timedelta(weeks=weeks)).strftime('%Y-%m-%d')
    start_date_min = df['timestamp'].min()
    # set start_date as the larger one from the start_date_delta and start_date_min 開始時間選資料最早時間與周數:兩者較晚者
    start_date = max(start_date_delta,   start_date_min)


    # (1) proceed filtering: a duration of a period of time
    # 期間條件
    period_condition = (df['timestamp'] >= start_date) & (df['timestamp'] <= end_date) 
    
    # (2) proceed filtering: news category
    # 新聞類別條件
    if (cate == "全部"):
        condition = period_condition  # "全部"類別不必過濾新聞種類
    else:
        # 過濾category新聞類別條件
        condition = period_condition & (df['category'] == cate)

    # (3) proceed filtering: and or
    # and or 條件
    if (cond == 'and'):
        # query keywords condition使用者輸入關鍵字條件and
        condition = condition & df['content'].apply(lambda text: all((qk in text) for qk in query_keywords)) #寫法:all()
    elif (cond == 'or'):
        # query keywords condition使用者輸入關鍵字條件
        condition = condition & df['content'].apply(lambda text: any((qk in text) for qk in query_keywords)) #寫法:any()
    # condition is a list of True or False boolean value
    df_query = df[condition]

    return df_query

def count_keyword(df_query:pd.DataFrame, query_keywords):

    cate_occurrence = {}
    cate_freq = {}
    
    news_categories = ['全部', 'AI', '雲端', '資安']
    # 字典初始化
    for cate in news_categories:
        cate_occurrence[cate] = 0   # {'政治':0, '科技':0}
        cate_freq[cate] = 0
        

    for idx, row in df_query.iterrows():
        # count the number of articles各類別篇數統計
        cate_occurrence[row['category']] += 1  #   {'政治':+1, '科技':0}
        cate_occurrence['全部'] += 1
        
        # count the keyword frequency各類別次數統計
        # 計算這一篇文章的content中重複含有多少個這些關鍵字(頻率)
        freq = sum([ len(re.findall(keyword, row['content'], re.I)) for keyword in query_keywords]) 
        cate_freq[row['category']] += freq # 在該新聞類別中累計頻率
        cate_freq['全部'] += freq  # 在"全部"類別中累計頻率

    total_articles = cate_occurrence['全部']  # len(df_query)
    total_frequency = cate_freq['全部']
    return cate_freq, cate_occurrence, total_articles, total_frequency

def get_keyword_occurrence_time_series(df_query):
    date_samples = df_query['timestamp']
    query_freq = pd.DataFrame({'date_index': pd.to_datetime(date_samples), 'freq': [1 for _ in range(len(df_query))]})
    data = query_freq.groupby(pd.Grouper(key='date_index', freq='D')).sum()
    line_xy_data = []
    for i, idx in enumerate(data.index):
        row = {'x': idx.strftime('%Y-%m-%d'), 'y': int(data.iloc[i].freq)}
        line_xy_data.append(row)
    return line_xy_data

def process_data_all_in_one(query_keywords, weeks):
    cond='or'
    cate='全部'

    df_query = filter_df_via_content(df, query_keywords, cond, cate, weeks)
    cate_freq, cate_occurrence, _, _ = count_keyword(df_query, query_keywords)
    freqByDate = get_keyword_occurrence_time_series(df_query)

    news_categories = ['全部', 'AI', '雲端', '資安']
    freqByCate = [cate_occurrence[k] for k in news_categories]

    response =  {'freqByDate': freqByDate,
            'freqByCate': freqByCate,
            'category': news_categories,
            'num_frequency': cate_freq['全部'], # 這關鍵字被提多少次
            'num_occurrence': cate_occurrence['全部'] #多少篇提到這關鍵字
            }
    return response

exist:bool = os.path.exists('app_fans/datasets/fans_data.csv')
if(exist == False):
    df = pd.read_csv('app_fans/datasets/ithome_news_preprocessed.csv',sep='|')
    query_keywords = ['網路風險','駭客','漏洞','入侵','資安'] #不要有子字串否則會重複計算 ['陳時中','時中']
    weeks=4

    data_response = process_data_all_in_one(query_keywords, weeks)
    df_data = pd.DataFrame(list(data_response.items()),columns=['name','value'])
    df_data.to_csv('app_fans/datasets/fans_data.csv',sep=',', index=None)

def load_data_fans():
    # Read data from csv file
    df_data = pd.read_csv('app_fans/datasets/fans_data.csv',sep=',')
    global response
    response = dict(list(df_data.values))
    del df_data

load_data_fans()

def home(request):
    return render(request,'app_fans/home.html', response)
