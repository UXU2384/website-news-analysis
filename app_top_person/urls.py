from django.urls import path
from app_top_person import views

app_name='app_top_person'
urlpatterns=[
    path('',views.home,name='home'),
    path('api_get_top_person/', views.api_get_top_person, name='api_top_person'),
    path('calculate_top_person/', views.calculate_top_person, name='calculate_top_person'),
]