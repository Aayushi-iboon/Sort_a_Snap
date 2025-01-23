from rest_framework import serializers
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from imagesense.serializers import UserProfileSerializer
# from imagesense.serializer.family_serializer import FamilySerializer
import base64
from rest_framework import serializers
from groups.model.group import CustomGroup, GroupMember,photo_group,PhotoGroupImage
from datetime import datetime
User = get_user_model()


    
    # def create(self, validated_data):
    #     # Automatically assign the authenticated user (if user is authenticated)
    #     validated_data['user'] = self.context['request'].user
    #     return super().create(validated_data)
    
    
    # def validate_user(self, value):
    #     if not isinstance(value, dict):
    #         raise serializers.ValidationError("The 'user' field must be a dictionary.")
    #     return value

    # def create(self, validated_data):
    #     # Extract nested user data``````````````````````````````````````````````````````
    #     # import ipdb;ipdb.set_trace()  
    #     user_data = validated_data.pop('user')
    #     # mobile_number = validated_data.get('phone_no')  
    #     # Create or update the user
    #     # print("=================>>>>>>>>>>.",mobile_number,user_data)
    #     user, created = User.objects.get_or_create(
    #         phone_no=user_data.get('phone_no'),
    #         defaults={
    #             "email": user_data.get("email", ""),
    #             "first_name": user_data.get("first_name", ""),
    #             "last_name": user_data.get("last_name", ""),
    #             "phone_no": user_data.get("phone_no", ""),
    #             "otp_status":True
    #         }
    #     )
    #     if not created:
    #         for key, value in user_data.items():
    #             setattr(user, key, value)
    #         user.save()
    #     validated_data["user_verified"] = True
    #     validated_data["user"] = user

    #     group_member = GroupMember.objects.create(**validated_data)
    #     return group_member
    
    # # def update(self, instance, validated_data):
    #     # import ipdb;ipdb.set_trace()
    #     user_data = validated_data.pop('user',{})
    #     user_data.pop('email', None)
    #     new_email = user_data.get('email', None)
    #     phone_no = user_data.get('phone_no', None)

      
    #     if new_email and new_email != instance.email:
    #         if User.objects.exclude(pk=instance.pk).filter(email=new_email).exists():
    #             raise serializers.ValidationError("Email address must be unique.")
            
    #     if new_email and instance.user.email and instance.user.email != new_email:
    #         raise serializers.ValidationError({"email": "Email cannot be updated once it's set."})

        
    #     if phone_no and instance.user.phone_no and instance.user.phone_no != phone_no:
    #         raise serializers.ValidationError({"phone_no": "Phone number cannot be updated once it's set."})

        
    #     for attr, value in user_data.items():
    #         # if attr not in ['email', 'phone_no']: 
    #         setattr(instance.user, attr, value)
        
    #     instance.user.save()
        
    #     instance.role = validated_data.get('role', instance.role)
    #     instance.group = validated_data.get('group', instance.group)
    #     instance.save()

    #     return instance
    
    # def to_representation(self, instance):
    #     request = self.context.get('request')
    #     from_method = self.context.get('from_method', 'unknown')

    #     def get_common_fields(instance):
    #         return {
    #             "role": instance.role,
    #             "joined_at": instance.joined_at,
    #         }

    #     common_fields = get_common_fields(instance)

    #     if request and request.method == 'GET' and 'pk'  in request.resolver_match.kwargs:
    #         # If specific group member details are requested
    #         member_data = {
    #             "id": instance.id,
    #             "group": instance.group.id,
    #             "user": instance.user.id,
    #             "role": instance.role,
    #             "joined_at": instance.joined_at,
    #             **common_fields,
    #         }
    #         return member_data

    #     elif from_method == 'list':
    #         # If listing all members with a simplified structure
    #         member_data = {
    #             "user": instance.user.id,
    #             "role": instance.role,
    #             "group_id": instance.group.id if instance.group else None,
    #             "group_name": instance.group.name if instance.group else None,
    #             **common_fields,
    #         }
    #         return member_data
        
    #     elif from_method == 'updates':
    #         member_data = {
    #             "user": instance.user.id,
    #             "first_name": instance.user.first_name,
    #             "last_name" : instance.user.last_name,
    #             # "role": instance.role,
    #             "group_id": instance.group.id if instance.group else None,
    #             "group_name": instance.group.name if instance.group else None,
    #              **common_fields,
    #         }
    #         return member_data
    #     else:
    #         # Default case: Provide basic member details
    #         member_data = {
    #             "id": instance.id,
    #             "group": instance.group.id,
    #             "user": instance.user.id,
    #             "role": instance.role,
    #             "joined_at": instance.joined_at,
    #             **common_fields,
    #         }
    #         return member_data

class GroupMemberSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer()  # Assuming this is a nested serializer for user data

    class Meta:
        model = GroupMember
        fields = ['id', 'group', 'user', 'role','roles', 'joined_at', 'user_verified']
        read_only_fields = ['joined_at']
    
    
    def validate_group(self, value):
        if not CustomGroup.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Group does not exist.")
        return value
    
    
    def create(self, validated_data):
        user_email = validated_data.pop('user')
        try:
            user = get_user_model().objects.get(email=user_email)
        except get_user_model().DoesNotExist:
            raise serializers.ValidationError({"user": "User with this email does not exist."})

        group_member = GroupMember.objects.create(user=user, **validated_data)
        return group_member
    
    def to_representation(self, instance):
        """
        Custom representation of the GroupMember model to include detailed group information.
        """
        request = self.context.get('request')
        from_method = self.context.get('from_method', 'unknown')

        # def get_common_fields(instance):
        #     """Helper function to extract common fields for all conditions."""
        #     return {
        #         "id": instance.id,
        #         "user_verified": instance.user_verified,
        #         "role": instance.role,
        #         "joined_at": instance.joined_at.strftime('%Y-%m-%d %H:%M:%S') if instance.joined_at else None,
        #     }

        # common_fields = get_common_fields(instance)

        if request and request.method == 'GET':
            # Detailed group information for GET requests
            group_data = {
                
                "id": instance.group.id,
                "name": instance.group.name,
                "access": instance.group.access,
                "code": instance.group.code,
                "thumbnail": instance.group.thumbnail.url if instance.group.thumbnail else None,
                "created_by": instance.group.created_by.email if instance.group.created_by else None,
                # "joined_at": instance.joined_at.strftime('%Y-%m-%d %H:%M:%S') if instance.joined_at else None,
                "created at": instance.joined_at.strftime('%Y-%m-%d %H:%M:%S') if instance.joined_at else None,
                
            }
            return group_data

        elif from_method == 'group_list':
            # Simplified structure for member listing
            group_data = {
                "group": {
                    "id": instance.group.id,
                    "name": instance.group.name,
                },
                "user": {
                    "id": instance.user.id,
                    "email": instance.user.email,
                },
            }
            return group_data
        elif from_method == 'created_group_list':
            group_data = {
                "id": instance.group.id,
                "name": instance.group.name,
                "access": instance.group.access,
                "code": instance.group.code,
                "thumbnail": instance.group.thumbnail.url if instance.group.thumbnail else None,
                "created_by": instance.group.created_by.email if instance.group.created_by else None,
                "created at": instance.joined_at.strftime('%Y-%m-%d %H:%M:%S') if instance.joined_at else None,
            }
            return group_data
        elif from_method == 'member_list':
            group_data = {
                "group_name": instance.group.name if instance.group else None,
                "user_id": instance.user.id if instance.user else None,
                "default_Admin": instance.group.created_by.id if instance.group.created_by else None,
                "default_Admin_email": instance.group.created_by.email if instance.group.created_by else None,
                "default_Admin_name": instance.group.created_by.first_name if instance.group.created_by else None,
                # "default_role" : instance.group.created_by.groups.name if instance.group.created_by else None,
                "default_role": instance.group.created_by.groups.last().name if instance.group and instance.group.created_by and instance.group.created_by.groups.exists() else None,
                "user_email": instance.user.email if instance.user else None,
                "user_profile":instance.user.profile_image.url if instance.user and instance.user.profile_image else None,
                "user_phone":instance.user.phone_no if instance.user else None,
                "role":instance.role if instance.role else None,
                "user_name":instance.user.first_name  if instance.user else instance.group.created_by.first_name
                
            }
            return group_data
        else:
            # Default representation
            group_data = {
                "group_id": instance.group.id,
                "group_name": instance.group.name,
                "user_id": instance.user.id,
                "user_email": instance.user.email,
                
            }
            return group_data
    
    
class CustomGroupSerializer(serializers.ModelSerializer):
    members = GroupMemberSerializer(source='groupmember_set', many=True, read_only=True)

    class Meta:
        model = CustomGroup
        fields = ['id', 'name', 'access', 'thumbnail', 'members','code','code_image','created_by']
        read_only_fields = ['code'] 
        
    def to_representation(self, instance):
        request = self.context.get('request')
        from_method = self.context.get('from_method', 'unknown')
        # import ipdb;ipdb.set_trace()
        def get_common_fields(instance):
            """Helper function to extract common fields for all conditions."""
            return {
                "name": instance.name,
                "access": instance.access,
                "thumbnail": instance.thumbnail.url if instance.thumbnail else None,
            }

        common_fields = get_common_fields(instance)
        created_at_str = instance.created_at.strftime('%Y-%m-%d %H:%M:%S') if instance.created_at else None
        if request and request.method == 'GET':
            # If specific group details are requested
            group_data = {
                "id": instance.id,
                "name": instance.name,
                "access": instance.access,
                "code": instance.code,
                "thumbnail": instance.thumbnail.url if instance.thumbnail else None,
                # "Created By": instance.created_by.id if instance.created_by else None,
                "Created By": instance.created_by.email if instance.created_by else None,
                'created at': created_at_str,
                'QR_code':instance.code_image.url if instance.code_image else None,
                # **common_fields,
            }
            return group_data

        elif from_method == 'member_group_list':
            # If listing all groups with a simplified structure
            group_data = {
                "name": instance.name,
                "access": instance.access,
                "Created By": instance.created_by.id if instance.created_by else None,
                **common_fields,
            }
            return group_data
        elif from_method == 'group_info':
            group_data = {
                "default_Admin_name": instance.name,
                "default_Admin_email":instance.email
                # "access": instance.access,
                # "Created By": instance.created_by.id if instance.created_by else None,
                # **common_fields,
            }
            return group_data
        
        elif from_method == 'list_groups':
            # If listing all groups with a simplified structure
            group_data = {
                "name": instance.name,
                "access": instance.access,
                **common_fields,
            }
            return group_data
        else:
            # Default case: Provide basic group details
            group_data = {
                "id": instance.id,
                "name": instance.name,
                "access": instance.access,
                "code": instance.code,
                "user_id": instance.created_by.id if instance.created_by else None,
                "user": instance.created_by.email if instance.created_by else None,
                "members": self.context.get('members', []),
                "thumbnail": instance.thumbnail.url if instance.thumbnail else None,
                'created at': created_at_str,
                'QR_code':instance.code_image.url if instance.code_image else None,
                **common_fields,
            }
            return group_data

class PhotoGroupImage_serializer(serializers.ModelSerializer):
    class Meta:
        model = PhotoGroupImage
        fields = ['id','image2','photo_group','fev']
    
    def to_representation(self, instance):
         # Default representation from the parent class
        representation = super().to_representation(instance)

        # Custom representation
        return {
            "id": instance.id, 
            "fev":instance.fev, 
            "image_url": getattr(instance.image2, 'url', None) if instance.image2 else None,
            "compress_url": getattr(instance.compressed_image, 'url', None) if instance.compressed_image else None,
            "photo_user_name": getattr(instance.photo_group.user, 'email', None) if instance.photo_group and instance.photo_group.user else None,
        }    
           
class photo_serializer(serializers.ModelSerializer):
    images = PhotoGroupImage_serializer(many=True) 
    class Meta:
        model = photo_group
        fields = '__all__'
    
    def create(self, validated_data):
        request = self.context.get('request')
        image = request.FILES.get('image')
        # import ipdb;ipdb.set_trace()
        if image is None:
            raise serializers.ValidationError({"image": "An image file is required."})
        validated_data.pop('image', None)
        try:
            try:
                group_member = photo_group.objects.create(**validated_data)
                group_member.image = image.read()
            except AttributeError:
                raise serializers.ValidationError({"image": "Uploaded file is invalid or corrupted."})
            group_member.save()
            return group_member
        except get_user_model().DoesNotExist:
            raise serializers.ValidationError({"user": "User with this email does not exist."})

    
    
    def update(self, instance, validated_data):
        # Check if image data is provided and decode it
        image_data = validated_data.get('image', None)
        if image_data:
            instance.image = base64.b64decode(image_data)
        instance.photo_name = validated_data.get('photo_name', instance.photo_name)
        instance.save()
        return instance
    
    def to_representation(self, instance):
        request = self.context.get('request')
        from_method = self.context.get('from_method', 'unknown')
        representation = super().to_representation(instance)
        images = representation.get('images', [])
        image_details = [
        {
            'id': img.get('id'),
            'image_url': img.get('image_url'),
            'fev': img.get('fev', False),
            'sub_group':img.get('sub_group')
        }
        for img in images
        ]
        # images_data = representation.get("images", [])
        if request and request.method == 'GET':
            # If specific group details are requested
            group_data = {
                "id": instance.id,
                "user":instance.user.email,
                "group": instance.group.name,
                "temp_name": instance.photo_name,
                "images": representation.get("images", [])
            }
            return group_data

        elif from_method == 'photo_image':
            # If listing all groups with a simplified structure
            group_data = {
                "id": instance.id,
                "user":instance.user.email,
                "group": instance.group.name,
                "temp_name": instance.photo_name,
                "images": representation.get("images", [])
            }
            return group_data
        # image_url
        if from_method == 'photo_image_list':
            self.context.setdefault('all_images', [])
            
            valid_images = [
                {   
                    "id": img.get("id"),
                    "image_url": img.get("image_url"),
                    "fev": bool(img.get("fev")),
                    'sub_group':img.get('sub_group')
                    
                }
                for img in image_details
                if isinstance(img, dict) and img.get('image_url')
            ]

            # Ensure unique images based on their URLs
            existing_image_urls = {img['image_url'] for img in self.context['all_images']}
            unique_images = [img for img in valid_images if img['image_url'] not in existing_image_urls]
            self.context['all_images'].extend(unique_images)

            return {"images": self.context.get('all_images', [])}

        
        elif from_method == 'photo_image_list_list':
            return {
                "id": instance.id,
                "fev": instance.fev,
                "image_url": getattr(instance.image2, 'url', None) if instance.image2 else None,
                "photo_user_name": getattr(instance.photo_group.user, 'email', None) if instance.photo_group and instance.photo_group.user else None,
            }     
        
        elif from_method == 'photo_image_group_list':
            # Initialize 'all_images' if not already present in the context
            self.context.setdefault('all_images', [])
            
            # Validate and filter valid images with 'image_url'
            valid_images = [img for img in (image_details or []) if isinstance(img, dict) and img.get('image_url')]
            
            # Deduplicate images by checking if the image is already in 'all_images'
            existing_image_urls = {img['image_url'] for img in self.context['all_images']}
            unique_images = [img for img in valid_images if img['image_url'] not in existing_image_urls]

            # Extend 'all_images' with unique images
            # self.context['all_images'].extend(unique_images)

            # Return the updated list of all images
            return {"images": unique_images}
            
        else:
            # Default case: Provide basic group details
            group_data = {
                "id": instance.id,
                "user":instance.user.email,
                "group": instance.group.name,
                "temp_name": instance.photo_name,
                "images": representation.get("images", [])
            }
            return group_data