from rest_framework import viewsets
from groups.model.group import photo_group,CustomGroup
from groups.serializers.group_serializers import photo_serializer,CustomGroupSerializer
from rest_framework.permissions import IsAuthenticated  
from rest_framework.response import Response
from rest_framework import status
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from face.function_call import StandardResultsSetPagination,Global_error_message,check_required_fields
import boto3
import base64
from django.http import Http404
from face.exceptions import CustomError
from face.function_call import ALLOWED_IMAGE_TYPES
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist


User = get_user_model()

rekognition_client = boto3.client('rekognition', region_name='us-west-2')  # Update the region as needed


def detect_faces(image_data):
    try:
        # Use AWS Rekognition to detect faces in the image
        response = rekognition_client.detect_faces(
            Image={'Bytes': image_data},  # Send image as bytes
            Attributes=['ALL']  # Optionally specify what you need (e.g., 'DEFAULT', 'ALL')
        )
        # Extract face details from the response
        return response.get('FaceDetails', [])
    except Exception as e:
        print(f"Error in Rekognition: {e}")
        return []


def binary_to_url(instance, request):
    try:
        binary_data = instance.photo_image.tobytes()  # Convert memory view to bytes
        file_path = f"images/photo_{instance.id}.jpg"  # Set the desired file path
        if default_storage.exists(file_path):
            default_storage.delete(file_path)  # Clean up old files
        file_name = default_storage.save(file_path, ContentFile(binary_data))
        url = request.build_absolute_uri(f"{settings.MEDIA_URL}{file_name}")
        return url
    except Exception as e:
        return None

class PhotoGroupViewSet(viewsets.ModelViewSet):
    queryset = photo_group.objects.all()
    serializer_class = photo_serializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter,DjangoFilterBackend]
    filterset_fields = ['photo_name']
    search_fields = ['photo_name']
    
    def get_queryset(self):
        return super().get_queryset()
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        try:
            if not queryset.exists():
                return Response({
                    "status": False,
                    "message": "No groups found!",
                    'data': []
                }, status=status.HTTP_204_NO_CONTENT)
                
            serializer = self.serializer_class(queryset, many=True, context={'request': request,'from_method':'photo_image'})
            return Response({
                "status": True,
                "message": "Groups retrieved successfully.",
                 'data': {"user_data":serializer.data}
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': "Something went wrong!",
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


    def get_list(self, request, *args, **kwargs):
        user = request.data.get('user')
        print(user)
        try:
            if not user:
                return Response(
                    {"status":False,'message': 'user is required in the request body'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user = get_user_model().objects.get(id=user) 
            photos = photo_group.objects.filter(user=user)
            serializer = self.get_serializer(photos, many=True,context={'request': request,'from_method':'photo_image_list'})
            return Response({ "status": True,  
                            "message": "get_ list Data retrieved successfully.",
                            "data":{"user_data":serializer.data}}, status=status.HTTP_200_OK)
        
        except ObjectDoesNotExist:
            return Response(
                {"status":False,'message': 'User not found',"data":None}, 
                status=status.HTTP_404_NOT_FOUND
            )

    # def get_all_group(self, request, *args, **kwargs):
    #     user_id = kwargs.get('user')
    #     try:
    #         if not user_id:
    #             return Response(
    #                 {"status": False, "message": "user is required."},
    #                 status=status.HTTP_400_BAD_REQUEST
    #             )
    #         User = get_user_model()
    #         user = User.objects.get(id=user_id)
    #         groups = CustomGroup.objects.filter(created_by=user)
    #         if not groups.exists():
    #             return Response(
    #                 {"status": False, "message": "No groups found for this user."},
    #                 status=status.HTTP_404_NOT_FOUND
    #             )
            
    #         # Serialize and return data
    #         serializer = CustomGroupSerializer(groups, many=True)
    #         return Response(
    #             {"status": True, "message": "Groups retrieved successfully.", "data": serializer.data},
    #             status=status.HTTP_200_OK
    #         )
    #     except User.DoesNotExist:
    #         return Response(
    #             {"status": False, "message": "User not found."},
    #             status=status.HTTP_404_NOT_FOUND
    #         )
    #     except Exception as e:
    #         return Response(
    #             {"status": False, "message": "something went wrong!","error" : str(e)},
    #             status=status.HTTP_500_INTERNAL_SERVER_ERROR
    #         )
            
            
    def get_group_wise_user(self, request, *args, **kwargs):
        user = request.data.get('user')
        group = request.data.get('group')
        if not user:
            return Response(
                {"status":False,'message': 'user_id is required '},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not group:
            return Response(
                {"status":False,'message': 'group is required '},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            photos = photo_group.objects.filter(user_id=user, group__id=group) if group else photo_group.objects.filter(user_id=user)
            if not photos.exists():
                return Response(
                    {"status":False,'message': 'No photos found for the given user and group'},
                status=status.HTTP_404_NOT_FOUND
            )
            serializer = self.get_serializer(photos, many=True)
            return Response({ "status": True,  
                             "message": "group and user wise Data retrieved successfully.",
                             "data":serializer.data}, status=status.HTTP_200_OK)
        
        except user.DoesNotExist:
            return Response(
                {"status": False,'message': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
              
    def create(self, request, *args, **kwargs):
        try:
            required_fields = ["photo_name","image","user","group"]
            error_message = check_required_fields(required_fields, request.data)
            if error_message:
                return Response({"status": False, "message": error_message},status=status.HTTP_400_BAD_REQUEST)
            image_file=request.FILES.getlist('image')
            if not image_file:
                return Response({"status": False, "message": "Uploaded 'image' file is invalid"},
                                status=status.HTTP_400_BAD_REQUEST)
            response_data = []
            for image in image_file:
                if image.content_type not in ALLOWED_IMAGE_TYPES:
                    return Response({"status": False, "message": f"Unsupported file type: {image.content_type}. Only JPG and PNG are allowed."},
                                    status=status.HTTP_400_BAD_REQUEST)
                    
            for image in image_file:
                try:
                    image_data = image.read()
                except Exception as e:
                    return Response({"status": False, "message": f"Error reading 'image': {str(e)}"},
                                    status=status.HTTP_400_BAD_REQUEST)
            
            
            data = request.data.copy()
            data['image'] = image_file
            serializer = self.serializer_class(data=data,context={'request': request})
            if serializer.is_valid():   
                photo_group = serializer.save()
                photo_group.save()
                # face_details = detect_faces(image_data)
                # photo_group.face_details = str(face_details) 
                # photo_group.save()
                return Response({'status': True, 'message': 'Upload photo successfully'},status=status.HTTP_201_CREATED)
            else:
                return Response({'status': False, 'message': 'Failed to upload photo', 'errors': serializer.errors},
                                status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'status':False,
                    'message':Global_error_message,
                    'error':str(e)}, status.HTTP_400_BAD_REQUEST)
    
    
    def update(self, request, *args, **kwargs):
        try:
            # Retrieve the instance to update
            photo_group = self.get_object()

            # Check for duplicate photo group name if necessary
            # photo_name = request.data.get('photo_name')
            # if PhotoGroup.objects.filter(photo_name=photo_name).exclude(id=photo_group.id).exists():
            #     return Response({"status": False, "message": "Photo name already exists."}, status=status.HTTP_400_BAD_REQUEST)

            # Create a copy of request data and remove the file entry if it exists
            data = request.data.copy()
            image_file = request.FILES.get('image', None)
            data.pop('image', None)
            if image_file:
                if image_file.content_type not in ALLOWED_IMAGE_TYPES:
                    return Response({"status": False, "message": f"Unsupported file type: {image_file.content_type}. Only JPG and PNG are allowed."},
                                    status=status.HTTP_400_BAD_REQUEST)
  
            serializer = self.serializer_class(photo_group, data=data, partial=True)

            if serializer.is_valid():
                updated_photo_group = serializer.save()
                if image_file:
                    try:
                        updated_photo_group.image = image_file.read()
                        updated_photo_group.save()
                    except Exception as e:
                        return Response({"status": False, "message": f"Error reading 'image': {str(e)}"},
                                        status=status.HTTP_400_BAD_REQUEST)

                return Response({'status': True, 'message': 'Photo group updated successfully'}, status=status.HTTP_200_OK)

            return Response({'status': False, 'message': 'Failed to update photo group', 'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'status': False,
                            'message': "An unexpected error occurred.",
                            'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
            
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            print("instance",instance)
            if instance:
                instance.delete()
            return Response({'status': True, 'message': 'photo deleted successfully'}, status=status.HTTP_200_OK)
        except Http404:
            return Response({'status': False, 'message': "User not found!"},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'status':False,
                    'message':"Something went wrong !!",
                    'error':str(e)},status=status.HTTP_400_BAD_REQUEST)


    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.serializer_class(instance, context={'request': request})
            logo_image = instance.image
            if logo_image:
                logo_path = f"logo_image/{instance.id}.jpg"
                if default_storage.exists(logo_path):
                    default_storage.delete(logo_path)
                default_storage.save(logo_path, ContentFile(logo_image))
                logo_image_url = request.build_absolute_uri(settings.MEDIA_URL + logo_path)
                data = serializer.data
                data['logo_image_url'] = logo_image_url
            else:
                data = serializer.data
                data['logo_image_url'] = None
            return Response({'status': True, 'message': 'Photo group data retrieved successfully.', 'data': data} ,status=status.HTTP_200_OK)
        except Http404:
            return Response({'status': False, 'message': 'Photo group list not found.'},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'status': False, 'message': Global_error_message, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
