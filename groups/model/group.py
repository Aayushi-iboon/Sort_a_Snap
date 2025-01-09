# from django.contrib.auth.models import Group
from django.db import models
# from django.contrib.auth.models import User
from django.conf import settings
import random
import os
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image

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
    code_image = models.ImageField(upload_to='QR_code/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.code:  # Only generate a code if it doesn't already exist
            self.code = self.generate_unique_code()
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(self.code)
        qr.make(fit=True)
        qr_image = qr.make_image(fill_color="black", back_color="white")
        # Save the QR code image to the code_image field
        qr_image_io = BytesIO()
        qr_image.save(qr_image_io, format="PNG")
        qr_image_name = f"{self.code}_qr.png"
        self.code_image.save(qr_image_name, ContentFile(qr_image_io.getvalue()), save=False)

        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_unique_code():
        while True:
            code = f"{random.randint(100000, 999999)}"
            if not CustomGroup.objects.filter(code=code).exists():
                return code



def user_image_upload_path(instance, filename):
    user_email = instance.photo_group.user.email  # Assuming `photo_group` has a `user` field
    if instance.photo_group.sub_group:
        # Use sub-group's name for the directory structure
        sub_group_name = instance.photo_group.sub_group.name  # Assuming `sub_group` has a `name` field
        group_name = instance.photo_group.group.name
        return os.path.join(f'photos/{user_email}/{group_name}/{sub_group_name}', filename)
    elif instance.photo_group.group:
        # Use group's name for the directory structure
        group_name = instance.photo_group.group.name  # Assuming `group` has a `name` field
        return os.path.join(f'photos/{user_email}/{group_name}', filename)
    else:
        # Default directory structure
        return os.path.join(f'photos/{user_email}', filename)



class sub_group(models.Model):
    main_group = models.ForeignKey(CustomGroup, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    access = models.CharField(max_length=50, null=True, blank=True, choices=CustomGroup.ACCESS_CHOICES)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True,blank=True)
    updated_at = models.DateTimeField(auto_now=True,null=True,blank=True)

    
    def __str__(self):
        return f"{self.name}"
    
    class Meta:
        db_table = "groups_sub_group"
        
        
class photo_group(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    group = models.ForeignKey(CustomGroup, on_delete=models.CASCADE)
    photo_name = models.CharField(max_length=255,blank=True)
    sub_group = models.ForeignKey(sub_group, related_name='sub_image', on_delete=models.CASCADE, null=True, blank=True)
    image = models.BinaryField(editable=True,blank=True,null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True,blank=True)
    updated_at = models.DateTimeField(auto_now=True,null=True,blank=True)
    
    def __str__(self):
        return self.photo_name or f"Photo {self.id}"

   
class GroupMember(models.Model):
    group = models.ForeignKey(CustomGroup, on_delete=models.CASCADE,related_name='groupmember_set')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  
    role = models.CharField(max_length=50,null=True,blank=True)
    user_verified = models.BooleanField(default=False) 
    joined_at = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return f"{self.user} - {self.group.name}"



        
class PhotoGroupImage(models.Model):
    photo_group = models.ForeignKey(photo_group, related_name='images', on_delete=models.CASCADE)
    sub_group = models.ForeignKey(sub_group,related_name="sub_group",on_delete=models.CASCADE,null=True,blank=True)
    # fav_images = models.ForeignKey(favorite_images,related_name='fev_images', on_delete=models.CASCADE,null=True,blank=True)
    fev = models.BooleanField(default=False)
    image2 = models.ImageField(upload_to=user_image_upload_path,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True,blank=True)
    updated_at = models.DateTimeField(auto_now=True,null=True,blank=True)
    
    def __str__(self):
        return f"{self.photo_group} - {self.image2}"
    
    
    
            

        