from rest_framework import serializers
from groups.model.group import PhotoGroupImage,sub_group



class PhotoSubGroupImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhotoGroupImage
        fields = ['id','image2','sub_group','photo_group','fav_images']

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Custom representation
        return {
            "id": instance.id,
            "image_url": instance.image2.url if instance.image2 else None,  
            "photo_user_name": instance.photo_group.user.email if instance.photo_group else None, 
            "fav_images":instance.fav_images.favorite if instance.fav_images else None
        }  

class SubPhotoGroupSerializer(serializers.ModelSerializer):
    # images = PhotoGroupImageSerializer(many=True, required=False)
    images_data = PhotoSubGroupImageSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = sub_group
        fields = ['id', 'main_group', 'access', 'created_by','name','images_data']

    def create(self, validated_data):
        images_data = self.context['request'].data.getlist('images')   
        user = validated_data.get('created_by')
        group = validated_data.get('main_group', None)
        if not group:
            validated_data['main_group'] = None
        photogroup = sub_group.objects.create(**validated_data)
        for i, image_file in enumerate(images_data):          
            if isinstance(image_file, (str, bytes)):
                raise ValueError("Invalid file data received.")
            else:
                PhotoGroupImage.objects.create(
                    photo_group=photogroup,
                    image2=image_file
                )
        return photogroup
