import re
import requests as rq
import pandas as pd
import time

from django.http import JsonResponse, HttpRequest
from django.shortcuts import render
from fake_useragent import UserAgent
from collections import Counter
from ckip_transformers.nlp import CkipWordSegmenter, CkipPosTagger, CkipNerChunker


# Create your views here.
#https://www.104.com.tw/jobs/search/?keyword=C%23&order=13&jobsource=joblist_search&page=1&area=6001016000&asc=0&jobexp=1&ro=1&searchJobs=1
def home(request):
    return render(request,'app_job/home.html')

user_agent = UserAgent()
keywords = ["C#", "Python", "JavaScript"]

def fetch_104_jobs(keyword="Python", page=1):
    url = "https://www.104.com.tw/jobs/search/list"
    params = {
        "ro": "0",  # 全職
        "keyword": keyword,
        "area": "6001001000",  # 高雄
        "exp": "1",  # 無經驗限制
        "page": str(page)
    }

    headers = {
        "User-Agent": user_agent.random,
        "Referer": "https://www.104.com.tw/jobs/search/"
    }

    res = rq.get(url, params=params, headers=headers, timeout=5)
    if res.ok:
        return res.json()["data"]["list"]
    else:
        print(f"請求失敗：{res.status_code}")
        return []

def jobs_to_dataframe(jobs, category:str):
    job_data = []
    for job in jobs:

        timestamp = job['appearDate']
        
        cont = job['description']
        cont = re.sub(r'◆\n*', '\n', cont)
        cont = re.sub(r'\xa0', '', cont)

        link = job['link']['job']
        

        job_data.append({
            'id': f'{category}_{timestamp}',
            "timestamp": job['appearDate'],
            'category': category,
            "title": job['jobName'],
            'content': cont,
            "company": job['custName'],
            "address": job['jobAddress'],
            "link": f"https://{link}",
            
        })
    return pd.DataFrame(job_data)

def api_get_job():

    df = pd.DataFrame()
    max_pages = 3

    for kw in keywords:
        print(f"🔍 搜尋關鍵字：{kw}")
        cate_jobs = []
        for page in range(1, max_pages + 1):
            jobs = fetch_104_jobs(keyword=kw, page=page)
            print(f"  第 {page} 頁：抓到 {len(jobs)} 筆")
            cate_jobs.extend(jobs)
            time.sleep(5)  # ⏱ 避免被封鎖

        df = pd.concat([df, jobs_to_dataframe(cate_jobs, kw)], ignore_index=True)
            
    df.drop_duplicates(subset=["link"], inplace=True)  # 去重複
    print(df.head())  # 預覽前幾筆
    df.to_csv("app_job/datasets/104_jobs.csv", sep='|', index=False, mode="a", header=False)
    print("✅ 已儲存成 DataFrame 並輸出為 104_jobs.csv")


def word_frequency(wp_pair, allowPOS):
    filtered_words = []
    for word, pos in wp_pair:
        if (pos in allowPOS) & (len(word) >= 2):
            filtered_words.append(word)
        #print('%s %s' % (word, pos))
    counter = Counter(filtered_words)
    return counter.most_common(200)

def ckiplab_word():
    ws = CkipWordSegmenter(model="albert-tiny")
    pos = CkipPosTagger(model="albert-tiny")
    ner = CkipNerChunker(model="albert-tiny")
    df = pd.read_csv('app_job/datasets/104_jobs.csv', sep='|')
    ## Word Segmentation
    tokens = ws(df.content)

    ## POS
    tokens_pos = pos(tokens)

    ## word pos pair 詞性關鍵字
    word_pos_pair = [list(zip(w, p)) for w, p in zip(tokens, tokens_pos)]

    ## NER命名實體辨識
    entity_list = ner(df.content)

    allowPOS = ['Na', 'Nb', 'Nc', 'VC']

    tokens_v2 = []
    for wp in word_pos_pair:
        tokens_v2.append([w for w, p in wp if (len(w) >= 2) and p in allowPOS])

    # Insert tokens into dataframe (新增斷詞資料欄位)
    df['tokens'] = tokens
    df['tokens_v2'] = tokens_v2
    df['entities'] = entity_list
    df['token_pos'] = word_pos_pair


    keyfreqs = []
    for wp in word_pos_pair:
        topwords = word_frequency(wp, allowPOS=allowPOS)
        keyfreqs.append(topwords)

    df['top_key_freq'] = keyfreqs

    # Abstract (summary) and sentimental score(摘要與情緒分數)
    summary = []
    sentiment = []
    for text in df.content:
        summary.append("暫無")
        sentiment.append("暫無")

    df['summary'] = summary
    df['sentiment'] = sentiment

    # Rearrange the colmun order for readability
    df = df[[
        'id', 'timestamp','category', 'title', 'content', 'sentiment', 'summary',
        'top_key_freq', 'tokens', 'tokens_v2', 'entities', 'token_pos', 'link',
        "company", "address"
    ]]

    # Save data to disk
    df.to_csv('app_job/datasets/104_preprocessed.csv', sep='|', index=False)
    print("Tokenize OK!")

def topkey_category():
    df = pd.read_csv('app_job/datasets/104_preprocessed.csv',sep='|')
    # Filter condition: two words and specified POS
    # 過濾條件:兩個字以上 特定的詞性
    allowedPOS=['Na','Nb','Nc']
    # Save top 20 word frequency for each category
    top_group_words = get_top_words(df,allowedPOS)
    df_top_group_words = pd.DataFrame(top_group_words, columns = ['category','top_keys'])
    df_top_group_words.to_csv('app_job/datasets/104_jobs_topkey_with_category_via_token_pos.csv', index=False)

#
# get topk keyword function
def get_top_words(df,allowedPOS):
    top_cate_words={} # final result
    counter_all = Counter() # counter for category '全部'
    for category in keywords:

        df_group = df[df.category == category]

        # concatenate all filtered words in the same category
        words_group = []
        for row in df_group.token_pos:

            # filter words for each news
            filtered_words =[]
            for (word, pos) in eval(row):
                if (len(word) >= 2) & (pos in allowedPOS):
                    filtered_words.append(word)

            # concatenate filtered words
            words_group += filtered_words

        # now we can count word frequency
        counter = Counter( words_group )

        # counter
        counter_all += counter
        topwords = counter.most_common(100)

        # store topwords
        top_cate_words[category]= topwords

    # Process category '全部'
    top_cate_words['ALL'] = counter_all.most_common(100)

    # To conveniently save data using pandas, we should convert dict to list.
    return list(top_cate_words.items())


# read df
df_topkey = pd.read_csv('app_job/datasets/104_jobs_topkey_with_category_via_token_pos.csv', sep=',')

# prepare data
data={}
for idx, row in df_topkey.iterrows():
    data[row['category']] = eval(row['top_keys'])

# We don't use it anymore, so delete it to save memory.
del df_topkey

# POST: csrf_exempt should be used
# 指定這一支程式忽略csrf驗證
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def api_get_job(request:HttpRequest):
    cate = request.POST.get('news_category')
    #cate = request.GET['news_category'] # this command also works.
    topk = request.POST.get('topk')
    topk = int(topk)
    print(cate, topk)

    chart_data, wf_pairs = get_category_job(cate, topk)
    response = {'chart_data': chart_data,
         'wf_pairs': wf_pairs,
         }
    return JsonResponse(response)

def get_category_job(cate, topk=10):
    wf_pairs = data[cate][0:topk]
    words = [w for w, f in wf_pairs]
    freqs = [f for w, f in wf_pairs]
    chart_data = {
        "category": cate,
        "labels": words,
        "values": freqs
    }
    return chart_data, wf_pairs

print("104_jobs--類別熱門關鍵字載入成功!")