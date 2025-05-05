from django.shortcuts import render
import pandas as pd
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
# Create your views here.
def home(request):
    return render(request,'app_top_person/home.html')

def load_data_top_person():
    df_top_person=pd.read_csv('app_top_person/dataset/itnews_top_person_by_category_via_ner.csv')
    global data
    data={}
    for i, row in df_top_person.iterrows():
        data[row['category']]=eval(row['top_keys'])

# Load data first when starting server.
load_data_top_person()

# csrf_exempt is used for POST
# 單獨指定這一支程式忽略csrf驗證
@csrf_exempt
def api_get_top_person(request):
    cate = request.POST.get('news_category')
    topk = request.POST.get('topk')
    topk = int(topk)

    chart_data, wf_pairs = get_category_top_person(cate, topk)
    response = {'chart_data':  chart_data,
                'wf_pairs': wf_pairs,}
    return JsonResponse(response)

def get_category_top_person(cate, topk):
    wf_pairs = data[cate][0:topk]
    words = [w for w, f in wf_pairs]
    freqs = [f for w, f in wf_pairs]
    chart_data = {
        "category": cate,
        "labels": words,
        "values": freqs}
    return chart_data, wf_pairs  # chart_data is for charting
