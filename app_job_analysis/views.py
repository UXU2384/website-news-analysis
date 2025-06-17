from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Max, Min, Count
from app_job.models import JobsData



# 3.1 前端統計頁面
def stats_page(request):
    latest_update = JobsData.objects.order_by('-updated_at').first()
    latest_time = latest_update.updated_at.strftime('%Y-%m-%d') if latest_update else '查不到最後更新時間!?'

    return render(request, 'app_job_analysis/stats.html', {'latest_time': latest_time})

from django.views.decorators.csrf import csrf_exempt

# 3.2 API：依程式語言分組，取最高薪資
@csrf_exempt
def api_top_by_lang(request):
    qs = JobsData.objects.values('category') \
            .annotate(max_salary=Max('salary')) \
            .order_by('-max_salary')
    data = list(qs)
    return JsonResponse(data, safe=False)

# 3.3 API：依公司分組，取最高薪資與相關資訊
def api_top_by_company(request):

    qs = JobsData.objects.order_by('-salary')

    seen = set()
    result = []
    for job in qs:
        if job.company not in seen:
            seen.add(job.company)
            result.append({
                'category': job.category,
                'company': job.company,
                'max_salary': job.salary,
                'title': job.title,
                'content': job.content,
                'link': job.link
            })
            if len(result) >= 10:
                break
    return JsonResponse(result, safe=False)

# 3.4 API：依日期分組，計算職缺數量
@csrf_exempt
def api_count_by_date(request):
    qs = JobsData.objects.values('updated_at')\
           .annotate(count=Count('id'))\
           .order_by('updated_at')
    data = [{'date': r['updated_at'].strftime('%m%d'), 'count': r['count']} for r in qs]
    return JsonResponse(data, safe=False)