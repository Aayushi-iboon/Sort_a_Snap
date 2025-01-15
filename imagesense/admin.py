from django.contrib import admin
from .models import User,BlackListToken
from .model import family
from .model.contact_us import ContactUs
from .model.privacypolicy import PrivacyPolicy
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm, UsernameField
# from .forms import UserCreationForm



@admin.register(User)
class UserAdmin(BaseUserAdmin):
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {'fields': ('email', 'slug', 'password')}),
        ('Personal Info', {'fields': ('phone_no', 'profile_image')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups','user_permissions', 'otp_status', 'otp_status_email', 'edit_profile'),
        }),
        ('Important Dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'slug', 'phone_no', 'profile_image', 'password1', 'password2'),
        }),
    )

    # Custom method to display groups
    def display_groups(self, obj):
        return ", ".join([group.name for group in obj.groups.all()])
    display_groups.short_description = 'Groups'

    # Update list_display to include custom group method
    list_display = (
        'id', 'email', 'slug', 'phone_no', 'is_staff', 'display_groups',
        'profile_image_tag', 'otp_status', 'first_name', 'last_name', 'otp_status_email'
    )
    list_display_links = ('id', 'email')


    list_filter = ('is_active', 'is_staff', 'groups', 'otp_status', 'otp_status_email')

    search_fields = ('email', 'slug', 'phone_no', 'otp_status_email')

    ordering = ('id',)


@admin.register(BlackListToken)
class BlackListedTokenAdmin(admin.ModelAdmin):
    readonly_fields = ['created_at']  # Ensure this field exists in your model
    list_display = ['user', 'token', 'created_at']
    

@admin.register(family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'relationship', 'user', 'profile_image','created_at')
    search_fields = ('name', 'relationship', 'user__email','created_at')
    list_filter = ('relationship',)
    readonly_fields = ('profile_image',)
    ordering = ('name',)

    def profile_image_display(self, obj):
        if obj.profile_image:
            return format_html('<img src="{}" width="50" height="50" />'.format(obj.profile_image.url))
        return "-"
    profile_image_display.short_description = 'Profile Image'






@admin.register(PrivacyPolicy)
class PrivacyPolicyAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_at']
    readonly_fields = ['created_at']
    fields = ['title', 'content', 'created_at']
    
    def has_add_permission(self, request):
        # Prevent adding more than one privacy policy instance
        if PrivacyPolicy.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the privacy policy instance
        return False
    
    
@admin.register(ContactUs)
class ContactUsAdmin(admin.ModelAdmin):
    list_display = ['id','name', 'email', 'message', 'phone_no']
    search_fields = ['id','name', 'email','phone_no']
    readonly_fields = ['created_at']
    
    