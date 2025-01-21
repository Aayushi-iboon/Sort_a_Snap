# my_app/serializers.py
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken, TokenError
from django.core.cache import cache
import hashlib
import logging
from imagesense.models import BlackListToken
from django.contrib.auth.password_validation import validate_password
import jwt
from rest_framework.exceptions import ValidationError
import re


logger = logging.getLogger(__name__)

User = get_user_model()

class OTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    phone_no = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        email = data.get('email')
        phone_no = data.get('phone_no')

        # Ensure that either email or phone_no is provided, but not both
        if (email and phone_no) or (not email and not phone_no):
            raise serializers.ValidationError("Provide either email or phone number, but not both.")
        
        if phone_no:
            # Check if the phone number starts with +91 and is followed by 10 digits
            if not re.match(r'^\+91\d{10}$', phone_no):
                raise serializers.ValidationError("Phone number must be in the format +91 followed by 10 digits.")
        
        if email:
            # Check if the email is a valid email address
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                raise serializers.ValidationError("Invalid email format.")
            
        return data 

class UserProfileSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False)

    
    class Meta:
        model = User
        fields = ['email', 'profile_image','first_name','last_name','date_joined','phone_no','edit_profile']
        # fields = "__all__"


    def update(self, instance, validated_data):
        profile_image = validated_data.pop('profile_image', None) 
        user = User(**validated_data)
        # user.edit_profile=True
        # user.save()
        if profile_image:
            instance.save_image(profile_image) 
            
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        instance.edit_profile=True
        instance.save()
        return instance

        
    def to_representation(self, instance):
        return {
            "id": instance.id,
            "email": instance.email,
            "first_name": instance.first_name,
            "last_name": instance.last_name,
            "profile_image": instance.profile_image.url if instance.profile_image else None,
            "phone_no": instance.phone_no,
        }


    def create(self, validated_data):
        profile_image = validated_data.pop('profile_image', None)
        
        user_instance = User.objects.create(**validated_data)
        
        if profile_image:
            user_instance.edit_profile=True
            user_instance.save_image(profile_image)  # Save the image using custom method
        
        return user_instance


        # def create(self, validated_data):
    #     sales_rap = validated_data.pop('sales_rap', None)
    #     new_lead_status = validated_data.get('leadstatus', None)
    #     new_sales_funnel_status = validated_data.get('salesfunnelstatus', None)
    #     doctor_id = validated_data.get('doctor_id')

    #     bright_sales_instance = bright_sales.objects.create(**validated_data)
        
    #     if sales_rap is not None:
    #         bright_sales_instance.sales_rap = sales_rap
    #         bright_sales_instance.save()

    #         try:
    #             doctor_instance = Doctor.objects.get(id=doctor_id.id)
    #         except ValidationError as e:
    #             raise serializers.ValidationError({"error": e.messages})

    #         doctor_instance.sales_rep_user = sales_rap
    #         doctor_instance.lead_status = new_lead_status
    #         doctor_instance.sales_funnel_status = new_sales_funnel_status
    #         doctor_instance.save()

    #     return bright_sales_instance
    

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField(required=False)
    user = serializers.IntegerField()
    token = serializers.CharField()

    def validate(self, attrs):
        self.refresh_token = attrs.get('refresh')
        self.access_token = attrs.get('access')  
        self.user = attrs.get('user')  
        self.token = attrs.get('token')
        return attrs

    def save(self, **kwargs):
        try:
            user_model = get_user_model()
            user = user_model.objects.get(id=self.user)
        except user_model.DoesNotExist:
            raise ValidationError({
                "status": False,
                "message": "User not found!"
            })
        try:
            token = RefreshToken(self.refresh_token)
            token.blacklist()
            cache_key =hashlib.sha256(self.token.encode()).hexdigest()
            cache.set(cache_key, "blacklisted", timeout=84600)
        except TokenError:
           
            raise ValidationError({
                "status": False,
                "message": "Token is not valid!"
            })

        if self.access_token:
            try:
                AccessToken(self.access_token).blacklist()
            except TokenError:
            
                raise ValidationError({
                    "status": False,
                    "message": "Token is not valid!"
                })

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return {
            'status': True,
            'message': 'Data retrieved successfully',
            'data': representation
        }