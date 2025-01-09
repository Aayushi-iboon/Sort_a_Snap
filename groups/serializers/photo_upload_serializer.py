
from rest_framework import serializers
from django.contrib.auth import get_user_model
import base64
from rest_framework import serializers
from groups.model.group import photo_group,PhotoGroupImage,sub_group
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
User = get_user_model()


class PhotoGroupImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhotoGroupImage
        fields = ['id','image2','fev']
    
    
    def to_representation(self, instance):
        # Default representation from the parent class
        representation = super().to_representation(instance)

        # Custom representation
        return {
            "id": instance.id,
            "image_url": instance.image2.url if instance.image2 else None,  
            "photo_user_name": instance.photo_group.user.email if instance.photo_group else None, 
            # "fav_images":instance.fav_images.favorite if instance.fav_images else None,
            'fev':instance.fev,
        }     

class PhotoGroupSerializer(serializers.ModelSerializer):
    # images = PhotoGroupImageSerializer(many=True, required=False)
    images_data = PhotoGroupImageSerializer(many=True, write_only=True, required=False)
    
    class Meta:
        model = photo_group
        fields = ['id', 'user', 'group','sub_group','photo_name','images_data']

    
    def create(self, validated_data):
        # Extract images and additional data
        images_data = self.context['request'].data.getlist('images')
        subgroup = validated_data.get('sub_group', None)
        group = validated_data.get('group', None)

        # If sub_group is provided, validate and associate it
        if subgroup:
            try:
                sub_group_instance = sub_group.objects.get(id=subgroup.id)
                validated_data['group'] = sub_group_instance.main_group  # Set the parent group
            except sub_group.DoesNotExist:
                raise serializers.ValidationError("Invalid sub_group ID.")

        photogroup = photo_group.objects.create(**validated_data)

        # Process images and save them without compression
        for image_file in images_data:
            if isinstance(image_file, (str, bytes)):
                raise ValueError("Invalid file data received.")
            else:
                PhotoGroupImage.objects.create(
                    photo_group=photogroup,
                    image2=image_file,  # Directly save the image without compression
                    fev=False
                )
        return photogroup

    
    def update(self, instance, validated_data):
        # Update the photo_name field if provided
        instance.photo_name = validated_data.get('photo_name', instance.photo_name)
        instance.save()

        # Get new images from the request
        images_data = self.context['request'].data.getlist('images')
        if images_data:
            # Get existing images for the photo group
            existing_images = PhotoGroupImage.objects.filter(photo_group=instance)
            existing_image_files = {img.image2.name for img in existing_images}

            # New images to be added
            new_images = []

            for image_file in images_data:
                if isinstance(image_file, (str, bytes)):
                    raise ValueError("Invalid file data received.")
                else:
                    # Check if this image already exists
                    if image_file.name not in existing_image_files:
                        new_images.append(
                            PhotoGroupImage(
                                photo_group=instance,
                                image2=image_file  # Add new image
                            )
                        )
                    else:
                        # Remove from the existing list to retain it
                        existing_image_files.remove(image_file.name)

            # Delete images that were not retained
            PhotoGroupImage.objects.filter(
                photo_group=instance,
                image2__in=list(existing_image_files)
            ).delete()

            # Add new images
            PhotoGroupImage.objects.bulk_create(new_images)

        return instance
    
    
    def to_representation(self, instance):
        
        representation = super().to_representation(instance)
        images = instance.images.all()  
        images_data = [
            {
                "id": image.id,
                "image_url": image.image2.url if image.image2 else None,  # Check if image2 exists
                "fev": image.fev # Include fav_images if it exists

            }
            for image in images
        ]
        representation['images'] = images_data
        return representation