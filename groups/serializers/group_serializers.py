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
        fields = ['id', 'group', 'user', 'role', 'joined_at', 'user_verified']
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
    
    
class CustomGroupSerializer(serializers.ModelSerializer):
    members = GroupMemberSerializer(source='groupmember_set', many=True, read_only=True)

    class Meta:
        model = CustomGroup
        fields = ['id', 'name', 'access', 'thumbnail', 'members','code','created_by']
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
                "Created By": instance.created_by.id if instance.created_by else None,
                **common_fields,
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
                **common_fields,
            }
            return group_data
        

class PhotoGroupImage_serializer(serializers.ModelSerializer):
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
        # import ipdb;ipdb.set_trace()
        representation = super().to_representation(instance)
        images = representation.get('images', [])
        image_details = [{'id': img.get('id'), 'image_url': img.get('image_url')} for img in images]
        images_data = representation.get("images", [])
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
        elif from_method == 'photo_image_list':
            group_data = {
                "images": image_details
            }
            return group_data
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
    
    # def update(self, instance, validated_data):
    #     request = self.context.get('request')
    #     image = request.FILES.get('image')
    #     # import ipdb;ipdb.set_trace()
    #     # Handle image file update
    #     if image:
    #         try:
    #             binary_data = image.read()
    #             instance.image = binary_data
    #         except Exception as e:
    #             raise serializers.ValidationError({"image": f"Error reading uploaded file: {str(e)}"})


    #     # Update other fields
    #     for attr, value in validated_data.items():
    #         setattr(instance, attr, value)

    #     # Save the updated instance
    #     instance.save()
    #     return instance