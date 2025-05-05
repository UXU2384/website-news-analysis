from django.urls import path
from app_user_keyword import views

app_name='app_user_keyword'
urlpatterns=[
    path('',views.home,name='home'),
    path('api_get_user_keyword/', views.api_get_user_keyword),
]