import app_user_keyword.views as userkeyword_views
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpRequest

from datetime import datetime, timedelta
import pandas as pd
import math
import re
from collections import Counter

def load_df_data():
    # import and use df from app_user_keyword
    global df  # global variable
    df = userkeyword_views.df


load_df_data()


# For the key association analysis
def home(request):
    return render(request, 'app_user_keyword_association/home.html')

# df_query should be global


@csrf_exempt
def api_get_userkey_associate(request:HttpRequest):
    request_data = request.POST
    
    userkey:str = request_data['userkey']
    cate = request_data['cate']
    cond = request_data['cond']
    weeks = int(request_data['weeks'])
    
    key = userkey.split()

    #global  df_query # global variable It's not necessary.

    df_query = filter_dataFrame_fullText(key, cond, cate, weeks)
    #print(key)
    print(len(df_query))

    if len(df_query) != 0:  # df_query is not empty
        newslinks = get_title_link_topk(df_query, k=10)
        related_words, clouddata = get_related_word_clouddata(df_query)
        same_paragraph = get_same_para(
            df_query, key, cond, k=6)  # multiple keywords
        num_articles=len(df_query) # total number of articles (stories, items)

    else:
        newslinks = []
        related_words = []
        same_paragraph = []
        clouddata = []
        num_articles=0

    response = {
        'num_articles': num_articles,
        'newslinks': newslinks,
        'related_words': related_words,
        'same_paragraph': same_paragraph,
        'clouddata': clouddata,
    }
    return JsonResponse(response)


# Searching keywords from "content" column
# Here this function uses df['content'] column, while filter_dataFrame() uses df.tokens_v2
def filter_dataFrame_fullText(user_keywords, cond, cate, weeks):

    # end date: the date of the latest record of news
    end_date = df['timestamp'].max()

    # start date
    start_date = (datetime.strptime(end_date, '%Y-%m-%d').date() -
                  timedelta(weeks=weeks)).strftime('%Y-%m-%d')

    # (1) proceed filtering: a duration of a period of time
    # 期間條件
    period_condition = (df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)

    # (2) proceed filtering: news category
    # 新聞類別條件
    if (cate == "全部"):
        condition = period_condition  # "全部"類別不必過濾新聞種類
    else:
        # category新聞類別條件
        condition = period_condition & (df['category'] == cate)

    # (3) proceed filtering: news category
    # and or 條件
    if (cond == 'and'):
        # query keywords condition使用者輸入關鍵字條件and
        condition = condition & df['content'].apply(lambda text: all(
            (qk in text) for qk in user_keywords))  # 寫法:all()
    elif (cond == 'or'):
        # query keywords condition使用者輸入關鍵字條件
        condition = condition & df['content'].apply(lambda text: any(
            (qk in text) for qk in user_keywords))  # 寫法:any()
    # condiction is a list of True or False boolean value
    df_query = df[condition]

    return df_query


# get titles and links from k pieces of news
def get_title_link_topk(df_query, k=25):
    items = []
    for i in range(len(df_query[0:k])):  # show only 10 news
        category = df_query.iloc[i]['category']
        title = df_query.iloc[i]['title']
        link = df_query.iloc[i]['link']
        photo = df_query.iloc[i]['photo']
        # if photo value is NaN, replace it with empty string
        if pd.isna(photo):
            photo = ''

        item_info = {
            'category': category,
            'title': title,
            'link': link,
            'photo': photo
        }

        items.append(item_info)
    return items

# Get related keywords by counting the top keywords of each news.
# Notice:  do not name function as  "get_related_keys",
# because this name is used in Django


def get_related_word_clouddata(df_query:pd.DataFrame):

    # wf_pairs = get_related_words(df_query)
    # prepare wf pairs
    counter = Counter()
    for idx in range(len(df_query)):
        pair_dict = dict(eval(df_query.iloc[idx]['top_key_freq']))
        counter += Counter(pair_dict)
    wf_pairs = counter.most_common(20)  # return list format

    # cloud chart data
    # the minimum and maximum frequency of top words
    min_ = wf_pairs[-1][1]  # the last line is smaller
    max_ = wf_pairs[0][1]
    # text size based on the value of word frequency for drawing cloud chart
    textSizeMin = 20
    textSizeMax = 120
    # 排除分母為0的情況
    # 這裡的min_是最小值，max_是最大值，這兩個值是頻率的大小
    if (min_ != max_):
        max_min_range = max_ - min_

    else:
        max_min_range = len(wf_pairs) # 關鍵詞的數量: 20個
        min_ = min_ - 1 # every size is 1 / len(wf_pairs)
    
    # word cloud chart data using proportional scaling
    # 排除分母為0的情況
    clouddata = [{'text':w, 'size':int(textSizeMin + (f - min_)/max_min_range * (textSizeMax-textSizeMin))} for w, f in wf_pairs]

    return wf_pairs, clouddata


# Step1: split paragraphs in text 先將文章切成一個段落一個段落
def cut_paragraph(text:str):
    paragraphs = text.split('。')  # 遇到句號就切開
    #paragraphs = re.split('。', text) # 遇到句號就切開
    #paragraphs = re.split('[。！!？?]', text) # 遇到句號(也納入問號、驚嘆號、分號等)就切開
    paragraphs = list(filter(None, paragraphs))
    return paragraphs

# Step2: Select all paragraphs where multiple keywords occur.


def get_same_para(df_query, user_keywords, cond, k=30):
    same_para = []
    for text in df_query['content']:
        #print(text)
        paragraphs = cut_paragraph(text)
        for para in paragraphs:
            para += "。"
            if cond == 'and':
                if all([re.search(kw, para) for kw in user_keywords]):
                    same_para.append(para)
            elif cond == 'or':
                if any([re.search(kw, para) for kw in user_keywords]):
                    same_para.append(para)
    return same_para[0:k]


print("app_user_keyword_association was loaded!")
