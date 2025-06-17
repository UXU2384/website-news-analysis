import ast
from django.db import models

# Create your models here.
from django.db import models

# Create your models here.
class JobsData(models.Model):
    # id|timestamp|category|title|content|
    # sentiment|summary|top_key_freq|tokens|
    # tokens_v2|entities|token_pos|link|
    # company|address|salary

    id = models.CharField(max_length=255, primary_key=True)
    category = models.CharField(max_length=100)

    timestamp = models.DateField()
    updated_at = models.DateField()

    title = models.TextField()
    content = models.TextField()

    sentiment = models.FloatField(null=True, blank=True)
    # summary = models.TextField(null=True, blank=True)
    top_key_freq = models.TextField(null=True, blank=True)  # Storing as string representation
    tokens = models.TextField(null=True, blank=True)
    tokens_v2 = models.TextField(null=True, blank=True)
    entities = models.TextField(null=True, blank=True)
    token_pos = models.TextField(null=True, blank=True)
    
    link = models.URLField(null=False, blank=True, unique=True)
    company = models.CharField(max_length=255)
    address = models.CharField(max_length=255)

    salary = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'JobsData'
        
    def __str__(self):
        return f"{self.timestamp}: {self.title}"
    
class JobCategoryTopKey(models.Model):
    category = models.CharField(max_length=100, unique=True)
    top_keys = models.JSONField()
    # created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category}: {self.top_keys}"
    
    def get_top_keys_as_list(self):
        """Convert the string representation of top_keys to a Python list of tuples"""
        try:
            return ast.literal_eval(self.top_keys)
        except:
            return []