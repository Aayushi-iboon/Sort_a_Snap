
from rest_framework import serializers
from django.contrib.auth import get_user_model
import base64
from rest_framework import serializers
from groups.model.group import photo_group,PhotoGroupImage
User = get_user_model()


class PhotoGroupImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhotoGroupImage
        fields = '__all__'

    def get_images_data(self, obj):
        images = obj.images.all()  # Get all related PhotoGroupImage instances
        return [{'id': image.id, 'image2': image.image2.url if image.image2 else None} for image in images]

class PhotoGroupSerializer(serializers.ModelSerializer):
    # images = PhotoGroupImageSerializer(many=True, required=False)
    images_data = PhotoGroupImageSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = photo_group
        fields = ['id', 'user', 'group', 'photo_name','images_data']

    def create(self, validated_data):
        images_data = self.context['request'].data.getlist('images')  
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
                "id": image.id,
                "image_url": image.image2.url if image.image2 else None  # Check if image2 exists
            }
            for image in images
        ]
        representation['images'] = images_data

        return representation