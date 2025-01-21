from django.db import models
from django.contrib.auth.models import Group,Permission
from django.contrib.auth.models import Permission
# Create your models here.
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager,PermissionsMixin
from django.db import models
from django.utils.text import slugify
from django.db.models.signals import pre_save
import time
import os
from django.utils.timezone import now
from django.utils.html import format_html
from django.conf import settings


class UserManager(BaseUserManager):
    def create_user(self, email, password='default', **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        return self.create_user(email, password, **extra_fields)



def get_timestamped_filename(instance, image):
    base, extension = os.path.splitext(image.name)
    timestamp = now().strftime('%Y%m%d%H%M%S')
    new_filename = f"{base}_{timestamp}{extension}"
    return os.path.join("profile_image", new_filename)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True,null=True, blank=True)
    first_name = models.CharField(max_length=50,null=True,blank=True)
    last_name = models.CharField(max_length=50,null=True,blank=True)
    edit_profile = models.BooleanField(default=False)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    otp_status = models.BooleanField(default=False)  # phone verify
    otp_status_email = models.BooleanField(default=False)  # email verify
    # slug = models.SlugField(unique=True, blank=True)  
    phone_no = models.CharField(max_length=15,null=True, blank=True,unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    # access = models.CharField(max_length=50,null=True,blank=True,choices=role)
    
    
    USERNAME_FIELD = 'email'
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='group wise permission to user',
        related_name='users',
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        blank=True,
        verbose_name='user permissions',
        related_name='user_permissions_set', 
        related_query_name='user_permissions',
    )

    objects = UserManager()


    def save_image(self, image_file):
        """Save image data as binary in the database."""
        self.profile_image = image_file
        self.save()
        # if image_file.size > 5 * 1024 * 1024:  # Limit image size to 5MB
        #     raise ValidationError("Image file too large ( > 5MB )")
        # self.image = image_file.read()
        # self.save() 

    def profile_image_tag(self):
        if self.profile_image:
            return format_html('<a href="{}" target="_blank"><img src="{}" width="100" height="100" /></a>',
                               self.profile_image.url, self.profile_image.url)
        return "No Image"

    profile_image_tag.short_description = 'Profile Image'

    
        
# def set_user_slug(sender, instance, *args, **kwargs):
#     if not instance.slug:
#         timestamp = int(time.time())  # Current Unix timestamp
#         email_prefix = instance.email.split('@')[0]
#         instance.slug = slugify(f"{email_prefix}-family-{timestamp}")


# pre_save.connect(set_user_slug, sender=User)


class BlackListToken(models.Model):
    token = models.CharField(max_length=500)
    user = models.ForeignKey(User, related_name="token_user", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)  # Optionally store expiration date

    def __str__(self):
        return f"Token {self.token} for user {self.user.email}"
    
# class Role(models.Model):
#     name=models.CharField(max_length=500,unique=True)
    
#     def __str__(self):
#         return self.name
    
# class UserRole(models.Model):
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="user_roles", on_delete=models.CASCADE)
#     role = models.ForeignKey(Role, related_name="role_users", on_delete=models.CASCADE)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(null=True, blank=True)

#     def __str__(self):
#         return f"{self.user.email} - {self.role.name}"
