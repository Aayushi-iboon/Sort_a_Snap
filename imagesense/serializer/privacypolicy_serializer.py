from rest_framework import serializers
from imagesense.model.privacypolicy import PrivacyPolicy
from imagesense.serializers import UserProfileSerializer


class policySerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivacyPolicy
        fields = ['id','title','content']