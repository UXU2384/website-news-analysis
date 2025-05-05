from django.urls import path
from app_job import views

app_name = 'app_job'

urlpatterns = [
    path('', views.home, name='home'),
    path('api_get_job/', views.api_get_job, name='api_job'),
]
