
from groups.model.group import sub_group
from rest_framework import serializers
# from serializers.photo_upload_serializer import PhotoGroupImageSerializer

class SubGroupSerializer(serializers.ModelSerializer):
    # images_data = PhotoGroupImageSerializer(many=True, write_only=True, required=False)
    class Meta:
        model = sub_group
        fields = '__all__'  
        
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user 
        return super().update(instance, validated_data)
    
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        group_data = {
            "id": instance.id,
            "master":instance.main_group.name if instance.main_group else None,
            "name": instance.name,
            "access": instance.access,
            "created_by": instance.created_by.email if instance.created_by else None,
            "created_at": instance.created_at,
            "updated_at": instance.updated_at,
        }
        return group_data