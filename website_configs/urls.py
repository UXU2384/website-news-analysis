from django.contrib import admin
from django.urls import path
from django.urls import include

urlpatterns = [
    path('topword/', include('app_top_keyword.urls')),
    path('topperson/', include('app_top_person.urls')),
    path('userkeyword/', include('app_user_keyword.urls')),
    path('fans/',include('app_fans.urls')),
    path('userkeywordassoc/',include('app_user_keyword_association.urls')),
    path('job/', include('app_job.urls')),
    path('sentiment/', include('app_sentiment.urls')),
    path('pk/', include('app_pk.urls')),
    path('userkeyword_db/', include('app_user_keyword_db.urls')),
    # admin 後台資料庫管理
    path('admin/', admin.site.urls),

]
