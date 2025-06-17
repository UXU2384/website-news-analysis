from django.db import models
from django.db import models
import ast

class TopPerson(models.Model):
    category = models.CharField(max_length=100)
    top_keys = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category}: {self.top_keys}"
    
    def get_top_keys_as_list(self):
        """Convert the string representation of top_keys to a Python list of tuples"""
        try:
            return ast.literal_eval(self.top_keys)
        except:
            return []