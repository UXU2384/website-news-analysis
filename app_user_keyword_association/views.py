import ast
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db.models import Q, Max, Min, F
from datetime import datetime, timedelta
import pandas as pd
import math
import re
from collections import Counter


from app_user_keyword_db.models import NewsData


# For the key association analysis
def home(request):
    return render(request, 'app_user_keyword_association/home.html')

# query_set should be global


@csrf_exempt
def api_get_userkey_associate(request:HttpRequest):
    request_data = request.POST
    
    userkey:str = request_data['userkey']
    cate = request_data['cate']
    cond = request_data['cond']
    weeks = int(request_data['weeks'])
    
    key = userkey.split()

    #global  query_set # global variable It's not necessary.

    query_set = filter_newsdata_fulltext(key, cond, cate, weeks)
    #print(key)
    print(len(query_set))

    if len(query_set) != 0:  # query_set is not empty
        newslinks = get_title_link_topk(query_set, k=10)
        related_words, clouddata = get_related_word_clouddata(query_set)
        same_paragraph = get_same_para(
            query_set, key, cond, k=6)  # multiple keywords
        num_articles=len(query_set) # total number of articles (stories, items)

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


def filter_newsdata_fulltext(user_keywords, cond, cate, weeks):
    # (1) 取得最新日期
    end_date = NewsData.objects.aggregate(max_time=Max('timestamp'))['max_time']
    if end_date is None:
        return pd.DataFrame()  # 如果資料為空

    end_date = end_date
    start_date = end_date - timedelta(weeks=weeks)

    # (2) 組合查詢條件：期間
    condition = Q(timestamp__gte=start_date, timestamp__lte=end_date)

    # (3) 組合查詢條件：分類
    if cate != "全部":
        condition &= Q(category=cate)

    # (4) 組合查詢條件：關鍵字 and / or
    if cond == 'and':
        for keyword in user_keywords:
            condition &= Q(content__icontains=keyword)
    elif cond == 'or':
        keyword_condition = Q()
        for keyword in user_keywords:
            keyword_condition |= Q(content__icontains=keyword)
        condition &= keyword_condition

    # (5) 查詢
    queryset = NewsData.objects.filter(condition).order_by('-timestamp')

    return queryset


def get_title_link_topk(query_set, k=25):
    items = []
    top_k_news = query_set[:k]  # ORM 支援 slicing

    for news in top_k_news:
        photo = news.photo if news.photo else ''
        item_info = {
            'category': news.category,
            'title': news.title,
            'link': news.link,
            'photo': photo
        }
        items.append(item_info)
    return items

# Get related keywords by counting the top keywords of each news.
# Notice:  do not name function as  "get_related_keys",
# because this name is used in Django


def get_related_word_clouddata(query_set):
    counter = Counter()
    for news in query_set:
        # top_key_freq 仍是字串，需要 eval 轉 dict
        pair_dict = dict(ast.literal_eval(news.top_key_freq))
        counter += Counter(pair_dict)

    wf_pairs = counter.most_common(20)  # top 20

    if not wf_pairs:
        return [], []

    min_ = wf_pairs[-1][1]
    max_ = wf_pairs[0][1]
    textSizeMin = 20
    textSizeMax = 120

    if min_ != max_:
        max_min_range = max_ - min_
    else:
        max_min_range = len(wf_pairs)
        min_ = min_ - 1

    clouddata = [
        {
            'text': w,
            'size': int(textSizeMin + (f - min_) / max_min_range * (textSizeMax - textSizeMin))
        }
        for w, f in wf_pairs
    ]

    return wf_pairs, clouddata



def cut_paragraph(text: str):
    paragraphs = re.split('[。！!？?]', text)  # 可以包含問號、驚嘆號等
    paragraphs = list(filter(None, paragraphs))
    return paragraphs

def get_same_para(query_set, user_keywords, cond, k=30):
    same_para = []
    for news in query_set:
        text = news.content
        paragraphs = cut_paragraph(text)
        for para in paragraphs:
            para += "。"
            if cond == 'and':
                if all(re.search(kw, para) for kw in user_keywords):
                    same_para.append(para)
            elif cond == 'or':
                if any(re.search(kw, para) for kw in user_keywords):
                    same_para.append(para)
            if len(same_para) >= k:
                return same_para[:k]
    return same_para[:k]


print("app_user_keyword_association was loaded!")
