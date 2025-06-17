from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import JobsData, JobCategoryTopKey

# Register your models here.
@admin.register(JobsData)
class JobsDataAdmin(admin.ModelAdmin):
    list_display = ('category', 'title', 'timestamp', 'company')

@admin.register(JobCategoryTopKey)
class JobCategoryTopKeyAdmin(admin.ModelAdmin):
    list_display = ('category', 'top_keys')