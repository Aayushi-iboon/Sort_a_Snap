# from django.contrib.auth.models import Group
from django.db import models
# from django.contrib.auth.models import User
from django.conf import settings
import random
import os
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image,ExifTags
from django.contrib.auth.models import Group
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
import boto3
import io
from django.core.files.uploadedfile import InMemoryUploadedFile


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

    class Meta:
        permissions = [
            ('download_QR_image', 'Can download QR image'),  
        ]

def user_image_upload_path(instance, filename):
    user_email = instance.photo_group.user.email  
    if instance.photo_group.sub_group:
        sub_group_name = instance.photo_group.sub_group.name  # Assuming `sub_group` has a `name` field
        group_name = instance.photo_group.group.name
        return os.path.join(f'photos/{group_name}/{sub_group_name}', filename)
    elif instance.photo_group.group:
        # Use group's name for the directory structure
        group_name = instance.photo_group.group.name  # Assuming `group` has a `name` field
        return os.path.join(f'photos/{group_name}', filename)
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
    role = models.CharField(
        max_length=50,
        choices=[("User", "User"), ("Group_Admin", "Group_Admin")],
        default="User"
    )
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
    compressed_image = models.ImageField(upload_to=user_image_upload_path, blank=True, null=True)  # Compressed version
    created_at = models.DateTimeField(auto_now_add=True,null=True,blank=True)
    updated_at = models.DateTimeField(auto_now=True,null=True,blank=True)
    
    def __str__(self):
        return f"{self.photo_group} - {self.image2}"
    
    class Meta:
        permissions = [
            ('download_image', 'Can download image'),  # New permission  
            ('fav_list','Can make favourite image')
        ]
        
    
    def save(self, *args, **kwargs):
        """Save original image and generate a compressed version only if `image2` is updated."""
        if self.pk:
            existing_instance = PhotoGroupImage.objects.filter(pk=self.pk).first()
            if existing_instance and existing_instance.image2 == self.image2:
                super().save(*args, **kwargs)
                return

        if self.image2:
            img = Image.open(self.image2)
            img_format = img.format  # Get the image format (JPEG, PNG, etc.)
            img_io = io.BytesIO()

            if img_format == "JPEG":
                img.save(img_io, format="JPEG", quality=20)  # Lossy compression
            elif img_format == "PNG":
                img = img.convert("RGBA")  # Preserve transparency
                img.save(img_io, format="PNG", optimize=True)  # Lossless compression
            else:
                raise ValueError("Unsupported image format. Only JPEG and PNG are allowed.")

            img_io.seek(0)

            # Generate compressed filename
            ext = os.path.splitext(self.image2.name)[-1]  # Get file extension
            compressed_filename = f"{self.image2.name.split('.')[0]}_compressed{ext}"

            # Save the compressed image
            self.compressed_image = InMemoryUploadedFile(
                img_io, "ImageField", compressed_filename,
                f"image/{img_format.lower()}", img_io.tell(), None
            )

        super().save(*args, **kwargs)
    # def save(self, *args, **kwargs):
    #     """Save original image and generate a compressed version only if `image2` is updated."""
    #     if self.pk:
    #         existing_instance = PhotoGroupImage.objects.filter(pk=self.pk).first()
    #         if existing_instance and existing_instance.image2 == self.image2:
    #             super().save(*args, **kwargs)
    #             return

    #     if self.image2:
    #         img = Image.open(self.image2)
    #         img_format = img.format  # Get the image format (JPEG, PNG, etc.)
            
    #         # Preserve EXIF metadata (to prevent image shifting issues)
    #         exif_data = img.info.get("exif", None)

    #         # Normalize orientation
    #         try:
    #             for orientation in ExifTags.TAGS.keys():
    #                 if ExifTags.TAGS[orientation] == "Orientation":
    #                     break
    #             if img._getexif() is not None:
    #                 exif = dict(img._getexif().items())
    #                 if orientation in exif:
    #                     if exif[orientation] == 3:
    #                         img = img.rotate(180, expand=True)
    #                     elif exif[orientation] == 6:
    #                         img = img.rotate(270, expand=True)
    #                     elif exif[orientation] == 8:
    #                         img = img.rotate(90, expand=True)
    #         except (AttributeError, KeyError, IndexError):
    #             pass  # No EXIF orientation data found

    #         # Ensure the image has a consistent size (prevent shifting)
    #         img = img.convert("RGB") if img_format == "JPEG" else img.convert("RGBA")
    #         width, height = img.size  # Keep original dimensions
            
    #         img_io = io.BytesIO()

    #         if img_format == "JPEG":
    #             img.save(img_io, format="JPEG", quality=20, exif=exif_data)  # Preserve EXIF
    #         elif img_format == "PNG":
    #             img.save(img_io, format="PNG", optimize=True)  # Lossless compression
    #         else:
    #             raise ValueError("Unsupported image format. Only JPEG and PNG are allowed.")

    #         img_io.seek(0)

    #         # Generate compressed filename
    #         ext = os.path.splitext(self.image2.name)[-1]  # Get file extension
    #         compressed_filename = f"{self.image2.name.split('.')[0]}_compressed{ext}"

    #         # Save the compressed image
    #         self.compressed_image = InMemoryUploadedFile(
    #             img_io, "ImageField", compressed_filename,
    #             f"image/{img_format.lower()}", img_io.tell(), None
    #         )

    #     super().save(*args, **kwargs)

            
# remove current deleting file
@receiver(pre_delete, sender=PhotoGroupImage)
def delete_s3_file(sender, instance, **kwargs):
    if instance.image2:
        s3_client = boto3.client("s3")
        s3_bucket = os.getenv("AWS_STORAGE_BUCKET_NAME")
        s3_file_key = instance.image2.name  # Get S3 file key (path)

        try:
            s3_client.delete_object(Bucket=s3_bucket, Key=s3_file_key)
            print(f"Deleted from S3: {s3_file_key}")
        except Exception as e:
            print(f"Error deleting from S3: {e}")
            
@receiver(pre_save, sender=PhotoGroupImage)
def delete_old_s3_file(sender, instance, **kwargs):
    """Delete old file from S3 when updating a new image"""
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            if old_instance.image2 and old_instance.image2 != instance.image2:
                s3_client = boto3.client("s3")
                s3_bucket = os.getenv("AWS_STORAGE_BUCKET_NAME")
                s3_client.delete_object(Bucket=s3_bucket, Key=old_instance.image2.name)
                print(f"Old image deleted from S3: {old_instance.image2.name}")
        except sender.DoesNotExist:
            pass