from rest_framework import viewsets
from groups.model.group import sub_group
from groups.serializers.sub_group_upload_serializer import SubPhotoGroupSerializer
from rest_framework.permissions import IsAuthenticated  
from rest_framework.response import Response
from rest_framework import status
from face.function_call import StandardResultsSetPagination,Global_error_message,check_required_fields
from rest_framework import filters
from groups.model.group import photo_group,PhotoGroupImage,GroupMember,CustomGroup,sub_group
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
User = get_user_model()

class PhotoSubGroupViewSet(viewsets.ModelViewSet):
    queryset = sub_group.objects.all()
    serializer_class = SubPhotoGroupSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter,DjangoFilterBackend]
    filterset_fields = ['name']
    search_fields = ['name']
    
    def get_queryset(self):
        return super().get_queryset()
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        try: 
            if not queryset.exists():
                return Response({
                    "status": False,
                    "message": "No groups found!",
                }, status=status.HTTP_204_NO_CONTENT)
                
            serializer = self.serializer_class(queryset, many=True, context={'request': request,'from_method':'photo_image'})
            return Response({
                "status": True,
                "message": "Folder retrieved successfully.",
                 'data': {"user_data":serializer.data}
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': "Something went wrong!",
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)




    def create_sub(self, request, *args, **kwargs):
        sub_group_id = request.data.get("sub_group_id")
        photo_group_id = request.data.get("photo_group_id")
        image = request.FILES.get("image2")

        if not sub_group_id or not photo_group_id or not image:
            return Response(
                {"error": "sub_group_id, photo_group_id, and image2 are required fields."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the sub_group instance
        sub_group_instance = get_object_or_404(sub_group, id=sub_group_id)

        # Create a new PhotoGroupImage instance
        photo_group_image = PhotoGroupImage.objects.create(
            sub_group=sub_group_instance,
            photo_group_id=photo_group_id,
            image2=image
        )

        # Serialize and return the newly created object
        serializer = self.get_serializer(photo_group_image)
        return Response(serializer.data, status=status.HTTP_201_CREATED)