
from face.function_call import StandardResultsSetPagination,Global_error_message,check_required_fields
from rest_framework import filters
from rest_framework import viewsets
from django.db.models.functions import Coalesce
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from ..serializer.privacypolicy_serializer import policySerializer
from imagesense.model.privacypolicy import PrivacyPolicy
from rest_framework.permissions import IsAuthenticated



class PrivacypolicyDataView(viewsets.ModelViewSet):
    queryset = PrivacyPolicy.objects.all()
    serializer_class = policySerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    
    
    def get_queryset(self):
        return super().get_queryset()
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        try:
            if not queryset.exists():
                return Response({
                    "status": False,
                    "message": "Data not found!",
                    'data': []
                }, status=status.HTTP_204_NO_CONTENT)

            serializer = self.serializer_class(queryset, many=True, context={'request': request,'from_method': 'user_family'})
            return Response({
                "status": True,
                "message": "Privacy Policy retrieved successfully.",
                'data': {"policy_data":serializer.data}
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': "Something went wrong!",
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    