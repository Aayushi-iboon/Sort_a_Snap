from django.urls import path
from django.conf import settings
from .view.group_views import CustomGroupViewSet,JoinGroupView
from .view.photouplaod_view import PhotoGroupViewSet
from .view.upload_photo_view import PhotoGroupView




urlpatterns = [
    path("get-customgroup-viewset/", CustomGroupViewSet.as_view({'get':'list'}), name="get_customgroup_viewset"),
    path("get-customgroup-viewset-create/", CustomGroupViewSet.as_view({'post':'create'}), name="customgroup_viewset_create"),
    path("get-customgroup-viewset-update/<int:pk>/", CustomGroupViewSet.as_view({'patch':'update'}), name="customgroup_viewset_update"),
    path("get-customgroup-viewset-delete/<int:pk>/", CustomGroupViewSet.as_view({'delete':'destroy'}), name="customgroup_viewset_delete"),
    path("get-customgroup-viewset-retrieve/<int:pk>/", CustomGroupViewSet.as_view({'get':'retrieve'}), name="customgroup_viewset_retrieve"),
    path("get-customgroup-viewset-userlist/", CustomGroupViewSet.as_view({'get':'userlist'}), name="get-customgroup-viewset-userlist"),
    
    path("photo-viewset-list/", PhotoGroupViewSet.as_view({'get':'list'}), name="photo_viewset_list"),
    path("photo-get-list/", PhotoGroupViewSet.as_view({'post':'get_list'}), name="photo_get_list"),
    path("get-group-wise-user/", PhotoGroupViewSet.as_view({'post':'get_group_wise_user'}), name="get_group_wise_user"),
    
    # do not use below 4 # working but not recomendate
    # path("upload-photo/", PhotoGroupViewSet.as_view({'post':'create'}), name="upload_photo"),
    # path("upload-photo/update/<int:pk>/", PhotoGroupViewSet.as_view({'patch':'update'}), name="update_upload_photo"),
    # path("upload-photo-delete/<int:pk>/", PhotoGroupViewSet.as_view({'delete':'destroy'}), name="upload_photo"),
    # path("upload-photo/retrieve/<int:pk>/", PhotoGroupViewSet.as_view({'get':'retrieve'}), name="update_upload_photo"),
    
    
    # use this working PhotoGroupView for single and multiple bulk upload
    path("photo-group-viewset-list/", PhotoGroupView.as_view({'get':'list'}), name="photo_viewset_list"),
    path("upload-group-photo/", PhotoGroupView.as_view({'post':'create'}), name="group_upload_photo"),
    path("upload-group-photo/update/<int:pk>/", PhotoGroupView.as_view({'patch':'update'}), name="update_group_upload_photo"),
    path("upload-group-photo-delete/<int:pk>/", PhotoGroupView.as_view({'delete':'destroy'}), name="delete_group_photo"),
    path("upload-group-photo/retrieve/<int:pk>/", PhotoGroupView.as_view({'get':'retrieve'}), name="group_retrive_photo"),
    
    
    
    path("create-customgroupmember-viewset/", JoinGroupView.as_view({'post':'join'}), name="create_customgroupmember_viewset"),
    path("generate-OTP-viewset/", JoinGroupView.as_view({'post':'user_verify'}), name="generate_OTP_viewset"),
    path("confirm-OTP-viewset/", JoinGroupView.as_view({'post':'user_confirm'}), name="confirm_OTP_viewset"),
    

    # path("get-customgroupmember-viewset/", GroupMemberViewSet.as_view({'get':'list'}), name="get_customgroupmember_viewset"),
    # path("update-customgroupmember-viewset/<int:pk>/", GroupMemberViewSet.as_view({'patch':'update'}), name="update_customgroupmember_viewset"),
    # path("delete-customgroupmember-viewset/<int:pk>/", GroupMemberViewSet.as_view({'delete':'destroy'}), name="destroy_customgroupmember_viewset"),
    # path("retrieve-customgroupmember-viewset/<int:pk>/", GroupMemberViewSet.as_view({'get':'retrieve'}), name="retrieve_customgroupmember_viewset"),
    # path("generate-OTP-viewset/", GroupMemberViewSet.as_view({'post':'user_verify'}), name="generate_OTP_viewset"),
    # path("confirm-OTP-viewset/", GroupMemberViewSet.as_view({'post':'user_confirm'}), name="confirm_OTP_viewset"),

]
