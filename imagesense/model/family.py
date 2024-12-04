from django.db import models
from django.conf import settings

class family(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name="family_members",null=True, blank=True)
    profile_image = models.ImageField(upload_to='family_images/', null=True, blank=True)
    name = models.CharField(max_length=50)
    relationship = models.CharField(max_length=50, help_text="Relationship to the user",null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} {self.relationship}"
    