from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated
import hashlib
from django.core.cache import cache
from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied
from groups.model.group import GroupMember
from django.contrib.auth.models import Permission
User = get_user_model()


class IsAuthenticat(IsAuthenticated):
    def has_permission(self, request, view):      
        is_authenticated = super().has_permission(request, view)
        if not is_authenticated:
            return False    
        is_allowed_user = True
        token = request.auth.get('jti')
        # print(token, 'token')
        cache_key = hashlib.sha256(token.encode()).hexdigest()
        # print(cache_key, 'cashkey')
        cached_data = cache.get(cache_key)
        if cached_data:
            is_allowed_user = False
        else:
            is_allowed_user = True
        return is_allowed_user
    

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_admin and user.is_active)



class GroupPermission(permissions.BasePermission):    
    def has_permission(self, request, view):
        user = request.user
        required_permission = getattr(view, 'required_permission', [])  
        
        if not required_permission:
            return True

        
        is_client_admin = not GroupMember.objects.filter(user=user).exists()
        
        if is_client_admin:
            return True  

        
        user_groups = GroupMember.objects.filter(user=user).select_related("group")
                
        if is_client_admin == False:    
            has_group_admin = user_groups.filter(role="Group_Admin").exists() 
            group_admin_has_permissions = has_group_admin and request.user.groups.filter(
                name="Group_Admin", permissions__codename__in=required_permission
                ).exists()
            
            if group_admin_has_permissions:
                return True 
            
            has_group_user = user_groups.filter(role="User").exists()
            group_user_has_permissions = has_group_user and request.user.groups.filter(
                name="User", permissions__codename__in=required_permission
                ).exists()
            
            if group_user_has_permissions:
                return True
            
            
        raise PermissionDenied({
            "status": False,
            "message": "You do not have the permission."
        })
