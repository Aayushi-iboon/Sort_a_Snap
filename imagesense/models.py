from django.db import models
from django.contrib.auth.models import Group,Permission
# Create your models here.

# my_app/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager,PermissionsMixin
from django.db import models
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.db.models.signals import pre_save
from phonenumber_field.modelfields import PhoneNumberField
import time
import os
from django.utils.timezone import now
from django.utils.html import format_html


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
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50,null=True,blank=True)
    last_name = models.CharField(max_length=50,null=True,blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    otp_status = models.BooleanField(default=False)  # phone verify
    otp_status_email = models.BooleanField(default=False)  # email verify
    slug = models.SlugField(unique=True, blank=True)  
    phone_no = models.CharField(max_length=15,null=True, blank=True,unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    # groups = models.ManyToManyField(
    #     Group,
    #     verbose_name='groups',
    #     blank=True,
    #     help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
    #     related_name='users',
    #     related_query_name='user',
    # )
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



class BlackListedToken(models.Model):
    token = models.CharField(max_length=500)
    user = models.ForeignKey(User, related_name="token_user", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("token", "user")
        
        
        
def set_user_slug(sender, instance, *args, **kwargs):
    if not instance.slug:
        timestamp = int(time.time())  # Current Unix timestamp
        email_prefix = instance.email.split('@')[0]
        instance.slug = slugify(f"{email_prefix}-family-{timestamp}")


pre_save.connect(set_user_slug, sender=User)

