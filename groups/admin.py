# from django.contrib import admin
# from django.contrib.auth.models import Group as AuthGroup
from django.contrib import admin
from django.contrib.auth.models import User
from groups.model.group import CustomGroup, GroupMember,photo_group,PhotoGroupImage,sub_group
from django.utils.html import format_html


# Inline model for managing group members within the CustomGroup admin page
class GroupMemberInline(admin.TabularInline):
    model = GroupMember
    extra = 1  # Number of empty forms to display
    fk_name = 'group'
    fields = ['user', 'role', 'joined_at']
    readonly_fields = ['joined_at']
    can_delete = False

# Custom Group admin to manage CustomGroup with additional fields
class CustomGroupAdmin(admin.ModelAdmin):
    list_display = ['id','name', 'access', 'thumbnail', 'created_by']
    search_fields = ['id','name', 'access']
    list_filter = ['access']
    inlines = [GroupMemberInline]

    def save_model(self, request, obj, form, change):
        if not obj.pk: 
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ['id','group', 'user', 'role', 'joined_at']
    search_fields = ['id','group__name', 'user__username', 'role']
    list_filter = ['id','role']
    readonly_fields = ['id','joined_at']
    
    
@admin.register(photo_group)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('id','photo_name','image', 'user', 'group', 'uploaded_at')
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="data:image/png;base64,{}" style="width: 100px; height: auto;" />',
                               obj.image.decode('utf-8'))  
        return "No Image"
    
    list_filter = ('group', 'uploaded_at')
    search_fields = ('photo_name', 'user__email', 'group__name')
    ordering = ('-uploaded_at',)

@admin.register(PhotoGroupImage)
class PhotoGroupImageAdmin(admin.ModelAdmin):
    """
    Admin configuration for the PhotoGroupImage model.
    """
    list_display = ('id', 'photo_group', 'image2','fev')  # Display related photo group and image
    list_filter = ('photo_group',)  # Filter by photo group
     # Enable search
    
  
@admin.register(sub_group)
class SubGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'main_group','created_by')
    list_filter = ('main_group','name' )
    search_fields = ('name','main_group')
    
    
    
# Register models in admin
# admin.site.register(PhotoGroupImage,PhotoGroupImageAdmin)
admin.site.register(CustomGroup, CustomGroupAdmin)
admin.site.register(GroupMember, GroupMemberAdmin)
