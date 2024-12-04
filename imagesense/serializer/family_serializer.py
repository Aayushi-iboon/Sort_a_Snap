from rest_framework import serializers
from imagesense.model.family import family
from imagesense.serializers import UserProfileSerializer


class FamilySerializer(serializers.ModelSerializer):
    # user = UserProfileSerializer()
    class Meta:
        model = family
        fields = '__all__'

    
    def to_representation(self, instance):
        request = self.context.get('request')
        from_method = self.context.get('from_method', 'unknown')
        def get_common_fields(instance):
            """Helper function to extract common fields for all conditions."""
            return {
                "name": instance.name,
                "relationship": instance.relationship,
                "profile_image": instance.profile_image.url if instance.profile_image else None
            }
        common_fields = get_common_fields(instance)

        if request and request.method == 'GET' and 'pk' in request.resolver_match.kwargs:
            # If specific family member details are requested
            user_data = instance.user
            family_data = {
                "id": instance.id,
                "name": instance.name,
                "relationship": instance.relationship,
                "profile_image": instance.profile_image.url if instance.profile_image else None,
                "user": {
                    "email": user_data.email,
                    "first_name": user_data.first_name,
                    "last_name": user_data.last_name,
                    "phone_no": user_data.phone_no,
                    "profile_image": user_data.profile_image.url if user_data.profile_image else None,
                },
                **common_fields,
            }
            return family_data

        elif from_method == 'user_family':
            # If listing all family members with a simplified structure
            user_data = instance.user
            family_data = {
                # "user": {
                #     "id": user_data.id,
                #     "full_name": f'{user_data.first_name} {user_data.last_name}',
                #     "email": user_data.email,
                # },
                "name": instance.name,
                "relationship": instance.relationship,
                **common_fields,
            }
            return family_data

        else:
            # Default case: Provide basic family details
            family_data = {
                "id": instance.id,
                "name": instance.name,
                "relationship": instance.relationship,
                "profile_image": instance.profile_image.url if instance.profile_image else None,
                **common_fields,
            }
            return family_data