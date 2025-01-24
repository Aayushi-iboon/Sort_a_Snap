
from rest_framework import serializers
from django.contrib.auth import get_user_model
import base64
from rest_framework import serializers
from groups.model.group import photo_group,PhotoGroupImage,sub_group
from PIL import Image
from io import BytesIO
from rest_framework.response import Response
from threading import Thread
from rest_framework import status
from django.core.files.uploadedfile import InMemoryUploadedFile
User = get_user_model()


class PhotoGroupImageSerializer(serializers.ModelSerializer):
    original_url = serializers.SerializerMethodField()
    compressed_url = serializers.SerializerMethodField()
    class Meta:
        model = PhotoGroupImage
        fields = ['id','image2','fev','original_url','compressed_url']
        
    def get_original_url(self, obj):
        return obj.image2.url if obj.image2 else None
    
    def get_compressed_url(self, obj):
        return obj.compressed_image.url if obj.compressed_image else None
    
    def to_representation(self, instance):
        # Default representation from the parent class
        representation = super().to_representation(instance)

        # Custom representation
        # import ipdb;ipdb.set_trace()
        return {
            "id": instance.id,
            "image_url": instance.image2.url if instance.image2 else None,  
            "compress_url": instance.compressed_image.url if instance.compressed_image else None,  
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

    
    # def create(self, validated_data):
    #     # Extract images and additional data
    #     images_data = self.context['request'].data.getlist('images')
    #     subgroup = validated_data.get('sub_group', None)
    #     group = validated_data.get('group', None)
        
    #     sub_group_instance = None  # Initialize the variable to avoid UnboundLocalError

    #     # If sub_group is provided, validate and associate it
    #     if subgroup:
    #         try:
    #             sub_group_instance = sub_group.objects.get(id=subgroup.id)
    #             validated_data['group'] = sub_group_instance.main_group  # Set the parent group
    #         except sub_group.DoesNotExist:
    #             raise serializers.ValidationError("Invalid sub_group ID.")

    #     # Create the photo group
    #     photogroup = photo_group.objects.create(**validated_data)

    #     # Process images and save them without compression
    #     for image_file in images_data:
    #         if isinstance(image_file, (str, bytes)):
    #             raise ValueError("Invalid file data received.")
    #         else:
    #             PhotoGroupImage.objects.create(
    #                 photo_group=photogroup,
    #                 sub_group=sub_group_instance,  # Will be None if not provided
    #                 image2=image_file,  # Directly save the image without compression
    #                 fev=False
    #             )
    #     return photogroup

    def create(self, validated_data):
        images_data = self.context['request'].data.getlist('images')
        user = self.context['request'].user 
        user_groups = user.groups.values_list('name', flat=True)        
        # if "Group_Admin" in user_groups:
        #     total_uploaded_images = PhotoGroupImage.objects.filter(photo_group__user=user).count()
        #     if total_uploaded_images + len(images_data) > 100:
        #         return Response(
        #             {"status": False, "message": "You have exceeded the maximum limit of 500 images."},
        #             status=status.HTTP_400_BAD_REQUEST
        #         )

        subgroup = validated_data.get('sub_group', None)
        sub_group_instance = None

        if subgroup:
            try:
                sub_group_instance = sub_group.objects.get(id=subgroup.id)
                validated_data['group'] = sub_group_instance.main_group  # Set the parent group
            except sub_group.DoesNotExist:
                raise serializers.ValidationError("Invalid sub_group ID.")

        
        photogroup = photo_group.objects.create(**validated_data)

        for image_file in images_data:
            if isinstance(image_file, (str, bytes)):
                raise serializers.ValidationError("Invalid file data received.")
            PhotoGroupImage.objects.create(
                photo_group=photogroup,
                sub_group=sub_group_instance,  # Will be None if not provided
                image2=image_file,  # Save the image
                fev=False
            )

        return photogroup
    
    def update(self, instance, validated_data):
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
                "compress_url": image.compressed_image.url if image.compressed_image else None,  # Check if image2 exists
                "fev": image.fev,
                "sub_group": representation['sub_group'],
                
            }
            for image in images
        ]
        representation['images'] = images_data
        return representation