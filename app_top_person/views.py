import ast
from datetime import timedelta
from typing import Counter
import pandas as pd

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db.models import Q, Max, F


from .models import TopPerson
from app_user_keyword_db.models import NewsData


# Create your views here.
def home(request):
    return render(request,'app_top_person/home.html')

allowedNE=['PERSON']
news_categories=['AI','雲端','資安']
def ne_word_frequency( a_news_ne ):
    filtered_words =[]
    for ner,word in a_news_ne:
        if (len(word) >= 2) & (ner in allowedNE):
            filtered_words.append(word)
    counter = Counter( filtered_words )
    return counter.most_common( 20 )

def NerToken(word, ner, idx):
    # print(ner,word)
    return ner,word


# csrf_exempt is used for POST
# 單獨指定這一支程式忽略csrf驗證
@csrf_exempt
def api_get_top_person(request):
    cate = request.POST.get('news_category')
    topk = request.POST.get('topk')
    topk = int(topk)

    calculate_top_person(request=request) 
    chart_data, wf_pairs = get_category_topPerson_db(cate, topk)
    response = {'chart_data':  chart_data,
                'wf_pairs': wf_pairs,}
    return JsonResponse(response)


# get charting data from database
def get_category_topPerson_db(cate, topk):
    # ORM   
    queryset = TopPerson.objects.filter(category=cate).values('top_keys')
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


def calculate_top_person(request):
    
    # Get the latest date in the database
    latest_date = NewsData.objects.aggregate(max_date=Max('timestamp'))['max_date']
    
    # Calculate start date
    start_date = latest_date - timedelta(weeks=4)  # 4 weeks ago
    
    top_cate_ner_words={}
    words_all=[]
    for category in news_categories:
        
        # Use Django's ORM to get entities for the given category
        entities_list = list(NewsData.objects
            .filter(category=category)
            .filter(timestamp__gte=start_date, timestamp__lte=latest_date)
            .values_list('entities', flat=True))
                
        # Process the retrieved entities
        words_group = []
        for entities in entities_list:
            if entities:  # Check if entities is not None
                words_group += eval(entities)

        # concatenate all terms
        words_all += words_group

        # Get top words by calling ne_word_frequency() function
        topwords = ne_word_frequency( words_group )
        top_cate_ner_words[category] = topwords

    topwords_all = ne_word_frequency(words_all)
    top_cate_ner_words['全部'] = topwords_all
    
    # save it to db
    for category, top_ners in top_cate_ner_words.items():
        # Convert the list of tuples to string representation for storage
        top_keys_str = str(top_ners)
        
        # Check if an entry for this category already exists
        try:
            # Update existing record
            obj = TopPerson.objects.get(category=category)
            obj.top_keys = top_keys_str
            obj.save()
        except TopPerson.DoesNotExist:
            # Create new record
            TopPerson.objects.create(
                category=category,
                top_keys=top_keys_str
            )
    
    messages.info(request, "Top person calculated and saved successfully")
    return redirect("app_top_person:home") 