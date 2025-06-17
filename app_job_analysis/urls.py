from django.urls import path
from . import views

app_name = 'app_job_analysis'

urlpatterns = [
    path('', views.stats_page, name='home'),      # 前端頁面
    path('api/top-by-lang/', views.api_top_by_lang, name='api_top_by_lang'),
    path('api/top-by-company/', views.api_top_by_company, name='api_top_by_company'),
    path('api/count-by-date/', views.api_count_by_date, name='api_count_by_date'),
]