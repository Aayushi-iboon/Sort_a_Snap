# my_app/serializers.py
from django.contrib.auth import get_user_model
from rest_framework import serializers
import logging
from django.contrib.auth.password_validation import validate_password

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

        return data

class UserProfileSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False)

    
    class Meta:
        model = User
        fields = ['email', 'profile_image','first_name','last_name','slug','date_joined','phone_no','edit_profile']
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