
from rest_framework import serializers
from django.contrib.auth import get_user_model
import base64
from rest_framework import serializers
from groups.model.group import photo_group,PhotoGroupImage
User = get_user_model()


class PhotoGroupImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhotoGroupImage
        fields = ['id','image2','photo_group']

    def to_representation(self, instance):
        # Default representation from the parent class
        representation = super().to_representation(instance)

        # Custom representation
        return {
            "id": instance.id,
            "image_url": instance.image2.url if instance.image2 else None,  
            "photo_user_name": instance.photo_group.user.email if instance.photo_group else None, 
        }     

class PhotoGroupSerializer(serializers.ModelSerializer):
    # images = PhotoGroupImageSerializer(many=True, required=False)
    images_data = PhotoGroupImageSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = photo_group
        fields = ['id', 'user', 'group', 'photo_name','images_data']

    def create(self, validated_data):
        images_data = self.context['request'].data.getlist('images')  
        user = validated_data.get('user')
        group = validated_data.get('group', None)
        if not group:
            validated_data['group'] = None
        photogroup = photo_group.objects.create(**validated_data)
        for i, image_file in enumerate(images_data):          
            if isinstance(image_file, (str, bytes)):
                raise ValueError("Invalid file data received.")
            else:
                PhotoGroupImage.objects.create(
                    photo_group=photogroup,
                    image2=image_file 
                )
        return photogroup

    
    def update(self, instance, validated_data):
        
        instance.photo_name = validated_data.get('photo_name', instance.photo_name)
        instance.save()

        
        images_data = self.context['request'].data.getlist('images')
        if images_data:
            
            PhotoGroupImage.objects.filter(photo_group=instance).delete()
            
            
            for image_file in images_data:
                if isinstance(image_file, (str, bytes)):
                    raise ValueError("Invalid file data received.")
                else:
                    PhotoGroupImage.objects.create(
                        photo_group=instance,
                        image2=image_file 
                    )
        return instance
    
    
    def to_representation(self, instance):
        
        representation = super().to_representation(instance)
        images = instance.images.all()  
        images_data = [
            {
                "image_url": image.image2.url if image.image2 else None  # Check if image2 exists
            }
            for image in images
        ]
        representation['images'] = images_data

        return representation