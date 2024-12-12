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
from face.function_call import StandardResultsSetPagination
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