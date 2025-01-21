
from face.function_call import StandardResultsSetPagination,Global_error_message,check_required_fields
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from ..serializer.contact_us_serializer import Contactus_Serializer
from imagesense.model.contact_us import ContactUs
from rest_framework.permissions import IsAuthenticated
from face.permissions import IsAuthenticat

class ContactusDataView(viewsets.ModelViewSet):
    queryset = ContactUs.objects.all()
    serializer_class = Contactus_Serializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticat]

    
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
                
            serializer = self.serializer_class(queryset, many=True, context={'request': request,'from_method': 'contact_us'})
            return Response({
                "status": True,
                "message": "Contact retrieved successfully.",
                'data': {"user_data":serializer.data} 
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': "Something went wrong!",
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def create(self, request, *args, **kwargs):
        try:
            required_fields = ["email","name","phone_no","message"]
           
            Contact_us_error_message = check_required_fields(required_fields, request.data)
            if Contact_us_error_message:
                return Response({"status": False, "message": Contact_us_error_message},status=status.HTTP_400_BAD_REQUEST)
            
            email = request.data.get('email')
            if ContactUs.objects.filter(email=email).exists():
                return Response({"status": False, "message": "Contact with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)

            serializer = self.serializer_class(data=request.data,context={'request': request,'from_method': 'list'})
            if serializer.is_valid():   
                contact=serializer.save()
                return Response({'status': True, 'message': 'Contact created successfully',"id":contact.id}, status=status.HTTP_201_CREATED)
            error_message = "some error"
            return Response({'status': False, 'message': 'Failed to create Contact', 'error':error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'status':False,
                    'message':Global_error_message,
                    'error':str(e)}, status.HTTP_400_BAD_REQUEST)
    
    
    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', True)
            instance = self.get_object()
            serializer = self.serializer_class(
                instance,
                data=request.data,
                partial=partial,
                context={'request': request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'status': True,
                    'message': 'Contact updated successfully',
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            return Response({
                'status': False,
                'message': 'Failed to update Contact',
                'errors': serializer.errors  
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print("Error during update:", str(e))
            return Response({
                'status': False,
                'message': 'An unexpected error occurred while updating contact',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
   
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.serializer_class(instance, context={'request': request})
            return Response({'status': True, 'message': 'Contact data retrieved successfully.', 'data': serializer.data} ,status=status.HTTP_200_OK)
        except Http404:
            return Response({'status': False, 'message': 'Data not found.'},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'status': False, 'message': Global_error_message, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    
        
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            print("instance",instance)
            if instance:
                instance.delete()
            return Response({'status': True, 'message': 'Contact deleted successfully'}, status=status.HTTP_200_OK)
        except Http404:
            return Response({'status': False, 'message': "Contact not found!"},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'status':False,
                    'message':Global_error_message,
                    'error':str(e)},status=status.HTTP_400_BAD_REQUEST)
    