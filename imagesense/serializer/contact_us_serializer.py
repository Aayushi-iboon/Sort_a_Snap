from rest_framework import serializers
from imagesense.model.contact_us import ContactUs
from imagesense.serializers import UserProfileSerializer


class Contactus_Serializer(serializers.ModelSerializer):
    class Meta:
        model = ContactUs
        fields = ['id','name','email','phone_no','message']
    
    def update(self, instance, validated_data):
        new_email = validated_data.get('email', instance.email)
        if new_email != instance.email:
            if ContactUs.objects.filter(email=new_email).exists():
                raise serializers.ValidationError({"email": "Contact Us with this email already exists."})
        return super().update(instance, validated_data)