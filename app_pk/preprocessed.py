import pandas as pd
from datetime import datetime, timedelta
import re

# Load Data 
df = pd.read_csv('app_sentiment/datasets/ithome_news_200_preprocessed.csv',sep='|')
# Step 0: Filter news articles using the following function
# Searching keywords from "content" column
def filter_df_via_content(df:pd.DataFrame, query_keywords, cond, cate, weeks):

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
        condition = period_condition & (df.category == cate)

    # (3) proceed filtering: and or
    # and or 條件
    if (cond == 'and'):
        # query keywords condition使用者輸入關鍵字條件and
        condition = condition & df['content'].apply(lambda text: all((qk in text) for qk in query_keywords)) #寫法:all()
    elif (cond == 'or'):
        # query keywords condition使用者輸入關鍵字條件
        condition = condition & df['content'].apply(lambda text: any((qk in text) for qk in query_keywords)) #寫法:any()
    # condiction is a list of True or False boolean value
    df_query = df[condition]

    return df_query

# Step 1: Sentimental polarity score計算整體情緒分數(影響力)
# sentimental polarity score
def get_article_sentiment(df_query):
    # df_query = df[df['tokens'].str.contains(query_key)]
    sentiCount = {'pos': 0, 'neg': 0, 'obj': 0}
    sentiPercnt = {'pos': 0, 'neg': 0, 'obj': 0}
    numberOfArticle = len(df_query)
    for senti in df_query['sentiment']:
        # 判斷文章的情緒極性
        if senti >= 0.75:
            sentiCount['pos'] += 1
        elif senti <= 0.4:
            sentiCount['neg'] += 1
        else:
            sentiCount['obj'] += 1
    for polar in sentiCount :
        sentiPercnt[polar]=round(sentiCount[polar]/numberOfArticle*100)

    return sentiCount, sentiPercnt

# **計算各類別多少篇文章提到該關鍵字
# **計算各類別出現關鍵字次數

news_categories = ['全部','AI', '雲端', '資安']



def count_keyword(df_query: pd.DataFrame, query_keywords):

    cate_occurrence = {}
    cate_freq = {}
    
    # 字典初始化
    for cate in news_categories:
        cate_occurrence[cate] = 0 
        cate_freq[cate] = 0

    for idx, row in df_query.iterrows():
        # count the number of articles各類別篇數統計
        cate_occurrence[row.category] += 1 
        cate_occurrence['全部'] += 1
        
        # count the keyword frequency各類別次數統計
        # 計算這一篇文章的content中重複含有多少個這些關鍵字(頻率)
        freq = sum([ len(re.findall(keyword, row.content, re.I)) for keyword in query_keywords]) 
        cate_freq[row.category] += freq # 在該新聞類別中累計頻率
        cate_freq['全部'] += freq  # 在"全部"類別中累計頻率

    total_articles = cate_occurrence['全部']  # len(df_query)
    total_frequency = cate_freq['全部']
    return cate_freq, cate_occurrence, total_articles, total_frequency

# 與上一週的程式碼有些不一樣，讓每個PK的對象之資料的start_date end_date都相同，折線圖才會完整
def get_keyword_occurrence_time_series(df_query):


    # end date: the date of the latest record of news
    end_date = df['timestamp'].max()
    
    # start date
    start_date_delta = (datetime.strptime(end_date, '%Y-%m-%d').date() - timedelta(weeks=weeks)).strftime('%Y-%m-%d')
    start_date_min = df['timestamp'].min()
    # set start_date as the larger one from the start_date_delta and start_date_min 開始時間選資料最早時間與周數:兩者較晚者
    start_date = max(start_date_delta,   start_date_min)
    

    # 設定時間欄位'date_index', 次數freq欄位，將每一篇的時間寫到'date_index'欄位，將freq設定為1 ==> 進行groupby之後就可以合併日期與加總freq次數
    query_freq = pd.DataFrame({'date_index':pd.to_datetime( df_query['timestamp'] ),'freq':[1 for _ in range(len(df_query))]})

    # 開始時間、結束時間兩項必須也加入到query_freq，計算次數時才會有完整的時間軸，否則時間軸長度會因為新聞時間不同，導致時間軸不一致
    dt_start_date = datetime.strptime(start_date, '%Y-%m-%d')
    dt_end_date = datetime.strptime(end_date, '%Y-%m-%d')   

    query_freq = pd.concat([query_freq, pd.DataFrame({'date_index': [dt_start_date], 'freq': [0]})])
    query_freq = pd.concat([query_freq, pd.DataFrame({'date_index': [dt_end_date], 'freq': [0]})])
    # query_freq = query_freq.append({'date_index': dt_end_date, 'freq': 0}, ignore_index=True)

    # 透過groupby就可以合併日期與加總freq次數
    freq_data_group = query_freq.groupby(pd.Grouper(key='date_index', freq='D')).sum()

    # 'date_index'為index(索引)，將其變成欄位名稱，inplace=True表示原始檔案會被異動
    freq_data_group.reset_index(inplace=True)
    # freq_data_group = freq_data_group.reset_index() # 這樣也可以得到同樣結果

    # 只有頻率次數值y, 沒有時間變數x, 計算相關係數時會用到
    # freq_data = freq_data_group.freq.to_list()

    # 有時間變數x,y，用於畫趨勢線圖
    line_xy_data = [{'x':date.strftime('%Y-%m-%d'),'y':freq} for date, freq in zip(freq_data_group.date_index,freq_data_group.freq)]

    return line_xy_data

# Step 4: Process PK data
# 定義PK對象
# 通常會多個關鍵字代表該PK對象，['柯文哲','柯p','柯P']
list_pkNames = ['網路', '資安', '企業']
list_pkKeywordSet = [['網路'], ['資安'], ['企業']]

# list_pkKeywordSet = [['網路'], ['資安'], ['企業'], ['柯文哲','柯p','柯P']]


# 線條顏色
list_colors = ["rgba(0,128,0,0.2)",'rgba(0,255,255,0.2)','rgba(0,0,255,0.2)']
#list_colors = ['green', 'red', 'blue']

# 人頭圖案
list_photos = [
    'https://blog.twnic.tw/wp-content/uploads/2022/07/%E5%85%AC%E9%96%8B%E7%B6%B2%E8%B7%AF%E4%B8%8A%E7%9A%84%E9%9A%B1%E7%A7%81%E5%AE%89%E5%85%A8-scaled.jpg',
    'https://cw-image-resizer.cwg.tw/resize/uri/https%3A%2F%2Fcdn-www.cw.com.tw%2Farticle%2F202207%2Farticle-62c7edd466a44.jpg/?w=1600&format=webp',
    'https://imgs.gvm.com.tw/upload/gallery/20220810/112806.jpg',
]

# 準備長條圖 線圖 總篇數 總次數等數據
list_freq_daily_line_chart = []
list_freq_news_category = []
list_sentimentInfo = []

list_total_articles=[]
list_total_frequency=[]

weeks = 12
cate = "全部"
cond = 'or'

selectedCategories = ['全部', 'AI','雲端','資安']
# selectedCategories = ['全部', 'AI','雲端','資安']

for query_keywords in list_pkKeywordSet:

    # Filter news   
    df_query = filter_df_via_content(df, query_keywords, cond, cate, weeks)
    #df_query = filter_df_via_tokens(df, query_keywords, cond, cate, weeks)
    
    # Get line chart data
    line_xy_data = get_keyword_occurrence_time_series(df_query)
    list_freq_daily_line_chart.append(line_xy_data)
    
    # Get bar chart data, total articals and frequecy 
    cate_freq, cate_occurrence, total_articles, total_frequency = count_keyword(df_query, query_keywords)
    list_total_articles.append(total_articles)
    list_total_frequency.append(total_frequency)


    # We select these categories to display: ['全部', 'AI','雲端','資安']
    cate_freq_selected = [cate_occurrence[cate] for cate in selectedCategories]
    list_freq_news_category.append(cate_freq_selected)

    # Get sentiment information
    sentiCount, sentiPercnt = get_article_sentiment(df_query)
    #sentiInfo = '正向:{}%, 中立:{}%, 負向:{}%'.format(str(sentiPercnt['pos']), str(sentiPercnt['obj']),
    #                                            str(sentiPercnt['neg']))
    senti_info = [sentiPercnt[p] for p in ['pos','obj','neg']] # 只要取用pos,obj, neg的情緒數字篇數百分比
    list_sentimentInfo.append(senti_info)

# We need all the following data to display on our frontend page 有一大堆數據要送到前端去展示啊
pk_data =  {'list_freq_daily_line_chart': list_freq_daily_line_chart,
           'list_pkNames': list_pkNames,
           'list_colors': list_colors,
           'list_photos': list_photos,
           'list_freq_news_category': list_freq_news_category,
           'list_category': selectedCategories,
           'list_sentiInfo': list_sentimentInfo,
           'list_total_articles': list_total_articles,
           'list_total_frequency': list_total_frequency
           }

# Step 5: Save PK data to csv file
df_data_pk = pd.DataFrame(list(pk_data.items()),columns=['name','value'])
## 存成csv格式檔案
df_data_pk.to_csv('app_pk/datasets/pk.csv',sep=',', index=None)