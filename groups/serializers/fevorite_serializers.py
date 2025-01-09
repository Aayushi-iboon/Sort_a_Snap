# from rest_framework import serializers
# from groups.model.group import favorite_images


# class Fev_image_Serializer(serializers.ModelSerializer):
#     class Meta:
#         model = favorite_images
#         fields = ['id','group','user','favorite','fevorite_image']
        
        
#     # def create(self, validated_data):
#     #     # If the 'favorite' is True, make sure to create a new instance
#     #     favorite = validated_data.get("favorite", False)
        
#     #     if favorite:
#     #         # If 'favorite' is True, we allow creating the favorite image
#     #         instance = favorite_images.objects.create(**validated_data)
#     #         return instance
#     #     else:
#     #         # If 'favorite' is False, we do not create the instance and can raise an error
#     #         raise serializers.ValidationError("Favorite must be True to create a new instance.")
        
    
#     # def update(self, instance, validated_data):
#     #     # Delete instance if 'favorite' is set to False
#     #     if validated_data.get('favorite') is False:
#     #         instance.delete()
#     #     else:
#     #         for attr, value in validated_data.items():
#     #             setattr(instance, attr, value)
#     #         instance.save()
#     #     return instance