from rest_framework import viewsets
from groups.model.group import sub_group
from groups.serializers.sub_group_serializers import SubGroupSerializer
from rest_framework.permissions import IsAuthenticated  
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models.functions import Coalesce
from rest_framework import filters
import logging
from face.function_call import StandardResultsSetPagination,check_required_fields
User = get_user_model()
logging.getLogger(__name__)

class SubGroupViewSet(viewsets.ModelViewSet):
    queryset = sub_group.objects.all()
    serializer_class = SubGroupSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter,DjangoFilterBackend]
    pagination_class = StandardResultsSetPagination
    filterset_fields = ['name']
    search_fields = ['name']

    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        try:
            if not queryset.exists():
                return Response({
                    "status": False,
                    "message": "No sub groups found!",
                    'data': []
                }, status=status.HTTP_204_NO_CONTENT)
                
            serializer = self.serializer_class(queryset, many=True)
            return Response({
                "status": True,
                "message": "Sub Group retrieved successfully.",
                'data': {"user_data":serializer.data} 
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': "Something went wrong!",
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def master_wise_sub_group_list(self, request, *args, **kwargs):
        master_id=kwargs.get("master_id")
        queryset = sub_group.objects.filter(main_group=master_id)
        try:
            if not queryset.exists():
                return Response({
                    "status": False,
                    "message": "No sub groups found!",
                    'data': []
                }, status=status.HTTP_204_NO_CONTENT)
                
            serializer = self.serializer_class(queryset, many=True)
            return Response({
                "status": True,
                "message": "Sub Group retrieved successfully.",
                'data': {"user_data":serializer.data} 
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': "Something went wrong!",
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def create(self, request, *args, **kwargs):
        required_fields = ["name"]
        upload_photo_error_message = check_required_fields(required_fields, request.data)
        if upload_photo_error_message:
            return Response({"status": False, "message": upload_photo_error_message},status=status.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        
        headers = self.get_success_headers(serializer.data)
        return Response({
            "status": True,
            "message": "Sub group created successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED, headers=headers)
        
    
    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', True)
            instance = self.get_object()              
            if 'user' in request.data:
                del request.data['user']  
            serializer = self.serializer_class(instance, data=request.data, partial=partial,context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response({'status': True, 'message': 'Family updated successfully', 'data': serializer.data}, status=status.HTTP_200_OK)
            return Response({'status': False, 'message': 'Failed to update Family', 'errors': ""}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'status':False,
                    'message':"something went wrong ",
                    'error':str(e)},status=status.HTTP_400_BAD_REQUEST)
            
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.serializer_class(instance)
            return Response({
                'status': True,
                'message': 'Sub Group data retrieved successfully.',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'Group not found.',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.delete()
            return Response({
                'status': True,
                'message': 'Sub Group deleted successfully.'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error deleting group.',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)