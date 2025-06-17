from fake_useragent import UserAgent
from collections import Counter
from ckip_transformers.nlp import CkipWordSegmenter, CkipPosTagger, CkipNerChunker
from datetime import datetime
import time
import ast
import re
import requests as rq


from django.http import JsonResponse, HttpRequest
from django.shortcuts import render


from app_job.models import JobsData, JobCategoryTopKey


def home(request):
    return render(request,'app_job/home.html')

user_agent = UserAgent()
keywords = ["C#", "Python", "JavaScript"]


def fetch_104_jobs(keyword="Python", page=1, start_date=30):
    url = "https://www.104.com.tw/jobs/search/list"
    params = {
        "ro": "1", # 全職
        "s9": "1",  # 日班
        "keyword": keyword,
        "area": "6001016000",  # 高雄
        "jobexp": "1",  # 1 年以下
        "page": str(page),
        "isnew": str(start_date),
        # "sctp": M # 月薪
        # "scmin": "35000", # 起薪
        "edu": "4", # 大學畢業
        "dep": "3006005000", # 資訊管理系相關
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


def extract_start_salary(text):
    # 正規表示式：匹配「月薪」開頭後面接一串數字（有可能有逗號）
    match = re.search(r"月薪\s*([\d,]+)", text)
    if match:
        # 移除逗號，轉成整數
        return int(match.group(1).replace(",", ""))
    return 28000

def jobs_to_db(jobs, category:str):

    for i, job in enumerate(jobs):

        cont = job['description']
        cont = re.sub(r'◆\n*', '\n', cont)
        cont = re.sub(r'\xa0', '', cont)
        cont = re.sub(r"<[^>]+>", "", cont)
        cont = re.sub(r'[\[\]]', '', cont)

        link = job['link']['job']

        timestamp = datetime.now().date()
        update_date = datetime.strptime(job["appearDate"], "%Y%m%d").date()

        full_link = f"https:{link}"
        JobsData.objects.update_or_create(
            link = full_link,
            defaults={
                "id": f"{category}_{timestamp}_{i}",
                "category": category,
                "timestamp": timestamp,
                "updated_at": update_date,
                "title": job["jobName"],
                "content": cont,
                "company": job["custName"],
                "address": job["jobAddrNoDesc"] + job["jobAddress"],
                "link": full_link,
                "salary": extract_start_salary(job["salaryDesc"])
            }
        )



def update_job():
    
    today = datetime.now().date()
    print(today)

    if JobsData.objects.filter(timestamp=today).exists():
        print("⏳ 今天已經更新過JobsData，跳過更新")
        return
    
    max_pages = 3

    for kw in keywords:
        print(f"🔍 搜尋關鍵字：{kw}")
        cate_jobs = []

        for page in range(1, max_pages + 1):
            jobs = fetch_104_jobs(keyword=kw, page=page)
            print(f"  第 {page} 頁：抓到 {len(jobs)} 筆")
            cate_jobs.extend(jobs)
            time.sleep(5)  # ⏱ 避免被封鎖

        jobs_to_db(cate_jobs, kw)

    # 建立模型
    ws = CkipWordSegmenter(model="albert-tiny")
    pos = CkipPosTagger(model="albert-tiny")
    ner = CkipNerChunker(model="albert-tiny")

    ckiplab_word(ws, pos, ner)
    topkey_category_orm_save()

    print("✅ 104 工作資料更新完畢")


def word_frequency(wp_pair, allowPOS):
    filtered_words = []
    for word, pos in wp_pair:
        if (pos in allowPOS) & (len(word) >= 2):
            filtered_words.append(word)
    counter = Counter(filtered_words)
    return counter.most_common(200)

def ckiplab_word(ws:CkipWordSegmenter, pos:CkipPosTagger, ner:CkipNerChunker):

    # 篩選今天的資料
    today = datetime.now().date()
    jobs = JobsData.objects.filter(timestamp=today)

    contents = [job.content for job in jobs]

    # CKIP 處理
    tokens = ws(contents)
    tokens_pos = pos(tokens)
    entity_list = ner(contents)

    allowPOS = ['Na', 'Nb', 'Nc', 'VC']
    word_pos_pair = [list(zip(w, p)) for w, p in zip(tokens, tokens_pos)]
    tokens_v2 = [[w for w, p in wp if len(w) >= 2 and p in allowPOS] for wp in word_pos_pair]

    # 頻率分析（你自定義的函數）
    keyfreqs = [word_frequency(wp, allowPOS=allowPOS) for wp in word_pos_pair]

    # 寫回資料庫
    for job, token, token_v2, wp, tf, ents in zip(jobs, tokens, tokens_v2, word_pos_pair, keyfreqs, entity_list):
        job.tokens = token
        job.token_pos = wp
        job.tokens_v2 = token_v2
        job.top_key_freq = tf
        job.entities = ents
        job.save()

    print("✅ 今天的職缺 NLP 分析完成！")


def topkey_category_orm_save():
    allowedPOS = ['Na', 'Nb', 'Nc']
    data = JobsData.objects.values_list('category', flat=True).distinct()
    top_group_words = get_top_words_orm(data, allowedPOS)

    # top_group_words 是 list of (category, top_keys)
    for category, top_keys in top_group_words:
        
        JobCategoryTopKey.objects.update_or_create(
            category=category,
            defaults={'top_keys': str(top_keys)}
        )
    print("✅ 已將分類 top keys 存入資料庫")

def get_top_words_orm(keywords, allowedPOS):
    
    top_cate_words = {}
    counter_all = Counter()

    for category in keywords:
        # 取出該分類的所有 Job，且 token_pos 不為空
        qs = JobsData.objects.filter(category=category).exclude(token_pos__isnull=True)

        words_group = []

        # 逐筆資料處理
        for job in qs.iterator():  # iterator避免載入過多資料進記憶體
            
            token_pos_list = ast.literal_eval(job.token_pos)

            flat_token_pos = [
                (word, pos)
                for word, pos in token_pos_list
                if isinstance(word, str) and isinstance(pos, str)
            ]

            filtered_words = [
                word for word, pos in flat_token_pos
                if len(word.strip()) >= 2 and pos in allowedPOS
            ]
            words_group.extend(filtered_words)

        counter = Counter(words_group)
        counter_all.update(counter)

        topwords = counter.most_common(100)
        top_cate_words[category] = topwords

    # '全部'分類詞頻
    top_cate_words['ALL'] = counter_all.most_common(100)
    print(top_cate_words)
    return top_cate_words.items()


update_job()


# POST: csrf_exempt should be used
# 指定這一支程式忽略csrf驗證
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def api_get_job(request:HttpRequest):
    cate = request.POST.get('news_category')
    #cate = request.GET['news_category'] # this command also works.
    topk = request.POST.get('topk')
    topk = int(topk)
    
    chart_data, wf_pairs = get_category_job_orm(cate, topk)
    response = {'chart_data': chart_data,
         'wf_pairs': wf_pairs,
         }
    return JsonResponse(response)


def get_category_job_orm(cate, topk=10):
    # ORM   
    queryset = JobCategoryTopKey.objects.filter(category=cate).values('top_keys')
    if queryset.exists():
        top_keys_str = queryset[0]['top_keys']
        wf_pairs = ast.literal_eval(top_keys_str)[0:topk]
    else:
        wf_pairs = []    
    
    words = [w for w, f in wf_pairs]
    freqs = [f for w, f in wf_pairs]
    chart_data = {
        "category": cate,
        "labels": words,
        "values": freqs}
    #print(chart_data)
    return chart_data, wf_pairs

print("104_jobs--類別熱門關鍵字載入成功!")

