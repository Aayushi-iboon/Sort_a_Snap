from django.urls import path
from django.conf import settings
from .view.group_views import CustomGroupViewSet,JoinGroupView
from .view.photouplaod_view import PhotoGroupViewSet
from .view.upload_photo_view import PhotoGroupView,PhotoGroupImageView
from .view.sub_group_upload_view import PhotoSubGroupViewSet
from .view.sub_group_views import SubGroupViewSet
# from .view.fevorite_view import FevoriteimageViewSet


urlpatterns = [
    path("get-customgroup-viewset/", CustomGroupViewSet.as_view({'get':'list'}), name="get_customgroup_viewset"),
    path("get-customgroup-viewset-create/", CustomGroupViewSet.as_view({'post':'create'}), name="customgroup_viewset_create"),
    path("get-customgroup-viewset-update/<int:pk>/", CustomGroupViewSet.as_view({'patch':'update'}), name="customgroup_viewset_update"),
    path("get-customgroup-viewset-delete/<int:pk>/", CustomGroupViewSet.as_view({'delete':'destroy'}), name="customgroup_viewset_delete"),
    path("get-customgroup-viewset-retrieve/<int:pk>/", CustomGroupViewSet.as_view({'get':'retrieve'}), name="customgroup_viewset_retrieve"),
    path("get-customgroup-viewset-userlist/<int:user>/", CustomGroupViewSet.as_view({'get':'userlist'}), name="get-customgroup-viewset-userlist"),
    path("get-customgroup-viewset-pagelist/", CustomGroupViewSet.as_view({'get':'list_page'}), name="get-customgroup-viewset-pagelist"),
    path("get-customgroup-viewset-family-member/<int:pk>/", CustomGroupViewSet.as_view({'get':'get_family_photos'}), name="get-customgroup-viewset-family_member"),
    path("download-QR/<int:pk>/", CustomGroupViewSet.as_view({'get':'download_QR_image'}), name="get-QR"),
    path('serve-group-image/<int:pk>/', CustomGroupViewSet.as_view({'get':'serve_image'}), name='download-qr-code'),
    
    
    
    path("photo-viewset-list/", PhotoGroupViewSet.as_view({'get':'list'}), name="photo_viewset_list"),
    path("photo-get-list/", PhotoGroupViewSet.as_view({'post':'get_list'}), name="photo_get_list"),
    path("get-group-wise-user/", PhotoGroupViewSet.as_view({'post':'get_group_wise_user'}), name="get_group_wise_user"),
    # path("group-list/<int:user>/", PhotoGroupViewSet.as_view({'post':'get_all_group'}), name="group-list"),
    
    
    # do not use below 4 # working but not recomendate
    # path("upload-photo/", PhotoGroupViewSet.as_view({'post':'create'}), name="upload_photo"),
    # path("upload-photo/update/<int:pk>/", PhotoGroupViewSet.as_view({'patch':'update'}), name="update_upload_photo"),
    # path("upload-photo-delete/<int:pk>/", PhotoGroupViewSet.as_view({'delete':'destroy'}), name="upload_photo"),
    # path("upload-photo/retrieve/<int:pk>/", PhotoGroupViewSet.as_view({'get':'retrieve'}), name="update_upload_photo"),
    
    
    # use this working PhotoGroupView for single and multiple bulk upload         
    path("photo-group-viewset-list/", PhotoGroupView.as_view({'get':'list'}), name="photo_viewset_list"),
    path("upload-group-photo/", PhotoGroupView.as_view({'post':'create'}), name="group_upload_photo"),
    # path("upload-sub-group-photo-image/", PhotoGroupView.as_view({'post':'create_sub'}), name="group_upload_photo"),
    path("upload-group-photo/update/<int:pk>/", PhotoGroupView.as_view({'patch':'update'}), name="update_group_upload_photo"),
    path("upload-group-photo-delete/<int:pk>/", PhotoGroupView.as_view({'delete':'destroy'}), name="delete_group_photo"),
    path("upload-group-photo/retrieve/<int:pk>/", PhotoGroupView.as_view({'get':'retrieve'}), name="group_retrive_photo"),
    path("photo-group-viewset-pagelist/", PhotoGroupView.as_view({'get':'list_page'}), name="photo_viewset_pagelist"),
    path("photo-group-viewset-access_group_images/<int:pk>/", PhotoGroupView.as_view({'get':'access_group_images'}), name="photo_viewset_access_group_images"),
    
    #upload data in sub folder or group 
                path("sub-group-viewset-list/", PhotoSubGroupViewSet.as_view({'get':'list'}), name="photo_viewset_list"),
                path("upload-group-sub-photos/", PhotoSubGroupViewSet.as_view({'post':'create'}), name="sub_group_upload_photo"),
                # path("upload-sub-group-photo-image/", PhotoSubGroupViewSet.as_view({'post':'create_sub'}), name="group_upload_photo"),
                # path("upload-group-sub-photo-delete/<int:pk>/", PhotoSubGroupView.as_view({'delete':'destroy'}), name="delete_sub_group_photo"),
                # path("upload-group-sub-photo/retrieve/<int:pk>/", PhotoSubGroupView.as_view({'get':'retrieve'}), name="sub_group_retrive_photo"),
    # path("photo-group-viewset-pagelist/", PhotoGroupView.as_view({'get':'list_page'}), name="photo_viewset_pagelist"),
    # path("photo-group-viewset-access_group_images/<int:pk>/", PhotoGroupView.as_view({'get':'access_group_images'}), name="photo_viewset_access_group_images"),
    
    
    path("get-subgroup-viewset-list/", SubGroupViewSet.as_view({'get':'list'}), name="get_subgroup_list"),
    path("subgroup-viewset-create/", SubGroupViewSet.as_view({'post':'create'}), name="get_subgroup_create"),
    path("subgroup-viewset-edit/<int:pk>/", SubGroupViewSet.as_view({'patch':'update'}), name="get_subgroup_edit"),
    path("subgroup-viewset-retrieve/<int:pk>/", SubGroupViewSet.as_view({'get':'retrieve'}), name="get_subgroup_retrieve"),
    path("subgroup-viewset-delete/<int:pk>/", SubGroupViewSet.as_view({'delete':'destroy'}), name="get_subgroup_destroy"),
    path("master-subgroup-viewset/<int:master_id>/", SubGroupViewSet.as_view({'get':'master_wise_sub_group_list'}), name="get_master_subgroup"),
    
    
    
    # path("get-subgroup-viewset/", SubGroupViewSet.as_view({'get':'list'}), name="get_subgroup_list"),
    
    
    path("create-customgroupmember-viewset/", JoinGroupView.as_view({'post':'join'}), name="create_customgroupmember_viewset"),
    path("generate-OTP-viewset/", JoinGroupView.as_view({'post':'user_verify'}), name="generate_OTP_viewset"),
    path("confirm-OTP-viewset/", JoinGroupView.as_view({'post':'user_confirm'}), name="confirm_OTP_viewset"),
    path("user-joined-group/", JoinGroupView.as_view({'get':'access_user_joined_group'}), name="user_joined_group"),
    path("member_list/", JoinGroupView.as_view({'post':'member_list'}), name="group_member_list"),
    path("promote_to_admin/", JoinGroupView.as_view({'post':'promote_to_admin'}), name="promote_t_admin"),
    path("demote_to_user/", JoinGroupView.as_view({'post':'demote_to_user'}), name="demote_t_user"),


    
    path("photo-group-image-viewset-list/", PhotoGroupImageView.as_view({'get':'list'}), name="photo_image_viewset_list"),
    path("photo-group-image-viewset-pagelist/", PhotoGroupImageView.as_view({'get':'list_page'}), name="photo_image_viewset_pagelist"),
    path("upload-group-image-photo/", PhotoGroupImageView.as_view({'post':'create'}), name="group_image_upload_photo"),
    path("fav-image-list/", PhotoGroupImageView.as_view({'post':'fav_list'}), name="fev_image_list"),
    path("upload-group-image-photo/update/<int:pk>/", PhotoGroupImageView.as_view({'patch':'update'}), name="update_group_image__upload_photo"),
    path("upload-group-image-photo-delete/<int:pk>/", PhotoGroupImageView.as_view({'delete':'destroy'}), name="delete_group_image_photo"),
    path("upload-group-image-photo/retrieve/<int:pk>/", PhotoGroupImageView.as_view({'get':'retrieve'}), name="group_retrive_image_photo"),
    path("upload-group-image-download_image/<int:pk>/", PhotoGroupImageView.as_view({'get':'download_image'}), name="downloadimage"),
    path('serve-specific-image/<int:pk>/', PhotoGroupImageView.as_view({'get':'serve_single_image'}), name='serve-image'),

    
    
    # path("fevourite-photos-viewset/", FevoriteimageViewSet.as_view({'get':'list'}), name="fevourite_photos_viewset"),
    # path("create-fevourite-photos-viewset/", FevoriteimageViewSet.as_view({'post':'create'}), name="create_fevourite_photos_viewset"),
    # path("update-fevourite-photos-viewset/<int:pk>/", FevoriteimageViewSet.as_view({'patch':'update'}), name="update_fevourite_photos_viewset"),
    # path("retrieve-fevourite-photos-viewset/<int:pk>/", FevoriteimageViewSet.as_view({'get':'retrieve'}), name="retrieve_fevourite_photos_viewset"),
    # path("remove-fevourite-photos-viewset/<int:pk>/", FevoriteimageViewSet.as_view({'delete':'destroy'}), name="remove_fevourite_photos_viewset"),
    # path("userwise-fevourite-photos-viewset/", FevoriteimageViewSet.as_view({'post':'userwise_fev_list'}), name="userwise_fevourite_photos_viewset"),



    # path("get-customgroupmember-viewset/", GroupMemberViewSet.as_view({'get':'list'}), name="get_customgroupmember_viewset"),
    # path("update-customgroupmember-viewset/<int:pk>/", GroupMemberViewSet.as_view({'patch':'update'}), name="update_customgroupmember_viewset"),
    # path("delete-customgroupmember-viewset/<int:pk>/", GroupMemberViewSet.as_view({'delete':'destroy'}), name="destroy_customgroupmember_viewset"),
    # path("retrieve-customgroupmember-viewset/<int:pk>/", GroupMemberViewSet.as_view({'get':'retrieve'}), name="retrieve_customgroupmember_viewset"),
    # path("generate-OTP-viewset/", GroupMemberViewSet.as_view({'post':'user_verify'}), name="generate_OTP_viewset"),
    # path("confirm-OTP-viewset/", GroupMemberViewSet.as_view({'post':'user_confirm'}), name="confirm_OTP_viewset"),

]
