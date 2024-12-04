from django.urls import path
from .views import GenerateOTP, VerifyOTP
from rest_framework.routers import DefaultRouter
from .views import UserProfileViewSet,LogoutView
from .view.family_view import FamilyDataView
from .view.privacypolicy_view import PrivacypolicyDataView
from .view.contact_us_view import ContactusDataView
from django.conf import settings




urlpatterns = [
    path("generate-otp/", GenerateOTP.as_view(), name="generate_otp"),
    path("verify-otp/", VerifyOTP.as_view(), name="verify_otp"),
    path('logout/', LogoutView.as_view({'post':'logout'}), name='logout'),

    
    path("edit-profile/<int:pk>/", UserProfileViewSet.as_view({'patch':'update'}), name="edit_profile"),
    path("delete-profile/<int:pk>/", UserProfileViewSet.as_view({'delete':'destroy'}), name="delete_profile"),
    path("get-profile/<int:pk>/", UserProfileViewSet.as_view({'get':'retrieve'}), name="get_profile"),
    path("verified-user-retrived/",UserProfileViewSet.as_view({'post':'verified_user_retrived'}),name="verified_user_retrived"),
    
    
    path("get-family/", FamilyDataView.as_view({'get':'list'}), name="get_family"),
    path("create-family/", FamilyDataView.as_view({'post':'create'}), name="create_family"),
    path("retrieve-family/<int:pk>/", FamilyDataView.as_view({'get':'retrieve'}), name="retrieve_family"),   
    path("edit-family/<int:pk>/", FamilyDataView.as_view({'patch':'update'}), name="edit_family"),   
    
    
    path("get-privacy-policy/", PrivacypolicyDataView.as_view({'get':'list'}), name="get_privacy_policy"),
    
    path("get-contact-us/", ContactusDataView.as_view({'get':'list'}), name="get_contact_us"),
    path("create-contact-us/", ContactusDataView.as_view({'post':'create'}), name="create_contact_us"),
    path("retrieve-contact-us/<int:pk>/", ContactusDataView.as_view({'get':'retrieve'}), name="retrieve_contact_us"),
    path("edit-contact-us/<int:pk>/", ContactusDataView.as_view({'patch':'update'}), name="edit_contact_us"),
    path("delete-contact-us/<int:pk>/", ContactusDataView.as_view({'delete':'destroy'}), name="delete_profile"),
    
    
]
