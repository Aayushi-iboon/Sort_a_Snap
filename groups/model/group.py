# from django.contrib.auth.models import Group
from django.db import models
# from django.contrib.auth.models import User
from django.conf import settings
import random
import os


class CustomGroup(models.Model):
    ACCESS_CHOICES = [ 
        ("1", "Private"),
        ("2", "Public"),
    ]
    name = models.CharField(max_length=255)
    access = models.CharField(max_length=50,null=True,blank=True,choices=ACCESS_CHOICES)
    thumbnail = models.ImageField(upload_to='groups/', blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_groups')
    code = models.CharField(max_length=10,unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.code:  # Only generate a code if it doesn't already exist
            self.code = self.generate_unique_code()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_unique_code():
        while True:
            code = f"{random.randint(100000, 999999)}"
            if not CustomGroup.objects.filter(code=code).exists():
                return code



class sub_group(models.Model):
    main_group = models.ForeignKey(CustomGroup, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    access = models.CharField(max_length=50, null=True, blank=True, choices=CustomGroup.ACCESS_CHOICES)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.name}"
    
    class Meta:
        db_table = "groups_sub_group"
        
# Function to generate the upload path for image2
def user_image_upload_path(instance, filename):
    # Ensure the directory structure is user-specific
    user_email = instance.photo_group.user.email
    return os.path.join(f'photos/{user_email}', filename)

class photo_group(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    group = models.ForeignKey(CustomGroup, on_delete=models.CASCADE)
    photo_name = models.CharField(max_length=255,blank=True)
    image = models.BinaryField(editable=True,blank=True,null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True,blank=True)
    updated_at = models.DateTimeField(auto_now=True,null=True,blank=True)
    
    def __str__(self):
        return self.photo_name or f"Photo {self.id}"

class PhotoGroupImage(models.Model):
    photo_group = models.ForeignKey(photo_group, related_name='images', on_delete=models.CASCADE)
    image2 = models.ImageField(upload_to=user_image_upload_path,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True,blank=True)
    updated_at = models.DateTimeField(auto_now=True,null=True,blank=True)

class GroupMember(models.Model):
    group = models.ForeignKey(CustomGroup, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  
    role = models.CharField(max_length=50,null=True,blank=True)
    user_verified = models.BooleanField(default=False) 
    joined_at = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return f"{self.user} - {self.group.name}"
