import ast
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Counter
import pandas as pd

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db.models import Q, Max, Min, F


from app_user_keyword_db.models import NewsData


def home(request):
    return render(request, 'app_sentiment/home.html')

# GET: csrf_exempt is not necessary
# POST: csrf_exempt should be used
@csrf_exempt
def api_get_sentiment(request):

    userkey:str = request.POST['userkey']
    cate = request.POST['cate']
    cond = request.POST['cond']
    weeks = int(request.POST['weeks'])
    print(weeks)

    query_keywords = userkey.split()
    response = prepare_for_response(query_keywords, cond, cate, weeks)
  
    return JsonResponse(response)

def prepare_for_response(query_keywords, cond, cate, weeks):

    # Proceed filtering
    query_set = filter_newsdata_via_content(query_keywords, cond, cate, weeks)
    
    sentiCount, sentiPercnt = get_article_sentiment(query_set)

    if weeks <= 4:
        freq_type = 'D'
    else:
        freq_type = 'W'

    line_data_pos = get_daily_basis_sentiment_count(query_set, sentiment_type='pos', freq_type=freq_type)
    line_data_neg = get_daily_basis_sentiment_count(query_set, sentiment_type='neg', freq_type=freq_type)

    response = {
        'sentiCount': sentiCount,
        'data_pos':line_data_pos,
        'data_neg':line_data_neg,
    }
    return response

def get_article_sentiment(queryset):
    sentiCount = {'Positive': 0, 'Negative': 0, 'Neutral': 0}
    sentiPercnt = {'Positive': 0, 'Negative': 0, 'Neutral': 0}

    # 抓出 sentiment 欄位的值
    sentiments = queryset.values_list('sentiment', flat=True)
    numberOfArticle = len(sentiments)

    for senti in sentiments:
        try:
            s = float(senti)
            if s >= 0.6:
                sentiCount['Positive'] += 1
            elif s <= 0.4:
                sentiCount['Negative'] += 1
            else:
                sentiCount['Neutral'] += 1
        except (TypeError, ValueError):
            continue  # 忽略無法轉成 float 的數值

    for polar in sentiCount:
        try:
            sentiPercnt[polar] = int(sentiCount[polar] / numberOfArticle * 100)
        except ZeroDivisionError:
            sentiPercnt[polar] = 0

    return sentiCount, sentiPercnt


def get_daily_basis_sentiment_count(queryset, sentiment_type='pos', freq_type='D'):
    if sentiment_type == 'pos':
        sentiment_check = lambda senti: 1 if senti >= 0.6 else 0
    elif sentiment_type == 'neg':
        sentiment_check = lambda senti: 1 if senti <= 0.4 else 0
    elif sentiment_type == 'neutral':
        sentiment_check = lambda senti: 1 if 0.4 < senti < 0.6 else 0
    else:
        return []

    # 建立統計用字典: key 是日期字串，value 是計數
    counter = defaultdict(int)

    # 從 QuerySet 提取時間與情緒欄位並處理
    for item in queryset.values('timestamp', 'sentiment'):
        ts = item['timestamp']
        senti = item['sentiment']
        date_key = ts.strftime('%Y-%m-%d')  # 依據日分群
        counter[date_key] += sentiment_check(senti)

    # 排序 & 格式化輸出
    result = [{'x': k, 'y': v} for k, v in sorted(counter.items())]
    return result

# Searching keywords from "content" column
# Here this function uses df['content'] column, while filter_dataFrame() uses df.tokens_v2
def filter_newsdata_via_content(query_keywords, cond, cate, weeks):
    # (1) 取得資料的最大與最小日期
    end_date:datetime = NewsData.objects.aggregate(max_time=Max('timestamp'))['max_time']
    start_date_min:datetime = NewsData.objects.aggregate(min_time=Min('timestamp'))['min_time']

    # 如果資料庫沒有資料，避免錯誤
    if end_date is None or start_date_min is None:
        return NewsData.objects.none()

    # (2) 計算起始日期
    start_date_delta = end_date - timedelta(weeks=weeks)
    start_date = max(start_date_delta, start_date_min)

    # (3) 建立 Q 查詢條件
    condition = Q(timestamp__gte=start_date) & Q(timestamp__lte=end_date)

    if cate != "全部":
        condition &= Q(category=cate)

    # (4) 關鍵字查詢條件 (使用 Q objects 和 icontains 或 contains)
    if cond == 'and':
        for kw in query_keywords:
            condition &= Q(content__icontains=kw)
    elif cond == 'or':
        keyword_q = Q()
        for kw in query_keywords:
            keyword_q |= Q(content__icontains=kw)
        condition &= keyword_q

    # (5) 執行查詢並回傳 QuerySet（如需轉 DataFrame 可加處理）
    queryset = NewsData.objects.filter(condition)

    return queryset


print("app_sentiment was loaded!")


