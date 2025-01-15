from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated
import hashlib
from django.core.cache import cache
from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied
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
        required_permission = getattr(view, 'required_permission', None)
        if required_permission is None:
            return True
        user_groups_permissions = request.user.groups.filter(
            permissions__codename__in=required_permission
        ).exists()
        if not user_groups_permissions:
            raise PermissionDenied(detail={
                "status" : False,
                "message": "You do not have permission to perform this action.",
            })

        return user_groups_permissions
    

# class IsClientAdmin(BasePermission):
#     """
#     Custom permission to allow only Client_Admin group members to upload photos.
#     """
#     def has_permission(self, request, view):
#         if not request.user.is_authenticated:
#             return False
#         return request.user.groups.filter(name="Client_Admin").exists()

