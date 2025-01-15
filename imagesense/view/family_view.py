from face.function_call import StandardResultsSetPagination,Global_error_message,check_required_fields
from rest_framework import filters
from rest_framework import viewsets
from django.db.models.functions import Coalesce
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from ..serializer.family_serializer import FamilySerializer
from imagesense.model.family import family
from django.db.models import Value
from django.db.models.functions import Replace
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
# from face.permissions import GroupPermission

# from django_filters.rest_framework import DjangoFilterBackend

class FamilyDataView(viewsets.ModelViewSet):
    queryset = family.objects.all()
    serializer_class = FamilySerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    # filter_backends = [filters.SearchFilter,DjangoFilterBackend]
    # filterset_fields = ['']
    # search_fields = ['']
    
    # def get_permissions(self):
    #     if self.action in ['create', 'retrieve','list']:
    #         print("self_action",self.action)
    #         self.required_permission = ['add_contactus']
    #         print("self_action",self.required_permission)
            
    #     return [IsAuthenticated(), GroupPermission()]
    
    def get_queryset(self):
        user_id = self.request.query_params.get('user_id', None)
        if user_id:
            # import ipdb;ipdb.set_trace()
            try:
                user = get_user_model().objects.get(id=user_id)
                return family.objects.filter(user=user)
            except get_user_model().DoesNotExist:
                return family.objects.none()
        else:            
            return super().get_queryset()
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        try:
            if not queryset.exists():
                return Response({
                    "status": False,
                    "message": "Data not found!",
                }, status=status.HTTP_204_NO_CONTENT)

            serializer = self.serializer_class(queryset, many=True, context={'request': request,'from_method': 'user_family'})
            return Response({
                "status": True,
                "message": "family Data retrieved successfully.",
                'data': {"user_data":serializer.data}
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': "Something went wrong!",
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

            
    def user_family(self, request, *args, **kwargs):
        user_email = self.request.query_params.get('user_email', None)
        pass

    
    def create(self, request, *args, **kwargs):
        try:
            org_required_fields = ["user","profile_image","name"]
            
            family_error_message = check_required_fields(org_required_fields, request.data)
            if family_error_message:
                return Response({"status": False, "message": family_error_message},status=status.HTTP_400_BAD_REQUEST)
        
    
            serializer = self.serializer_class(data=request.data,context={'request': request,'from_method': 'list'})
            if serializer.is_valid():   
                serializer.save()
                return Response({'status': True, 'message': 'family created successfully'}, status=status.HTTP_201_CREATED)
            error_message = ' '.join([f"{field}: {', '.join([str(e) for e in errors])}" for field, errors in serializer.errors.items()])
            return Response({'status': False, 'message': 'Failed to create family', 'error':error_message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'status':False,
                    'message':Global_error_message,
                    'error':str(e)}, status.HTTP_400_BAD_REQUEST)
    
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.serializer_class(instance, context={'request': request})
            return Response({'status': True, 'message': 'family data retrieved successfully.', 'data': serializer.data} ,status=status.HTTP_200_OK)
        except Http404:
            return Response({'status': False, 'message': 'Data not found.'},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'status': False, 'message': Global_error_message, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', True)
            # import ipdb;ipdb.set_trace()
            instance = self.get_object()  
           
            
            if 'user' in request.data:
                del request.data['user']  
                
            serializer = self.serializer_class(instance, data=request.data, partial=partial,context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response({'status': True, 'message': 'Family updated successfully', 'data': serializer.data}, status=status.HTTP_200_OK)
            
            error_message = ' '.join([f"{field}: {', '.join([str(e) for e in errors])}" for field, errors in serializer.errors.items()])
            return Response({'status': False, 'message': 'Failed to update Family', 'errors': ""}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'status':False,
                    'message':Global_error_message,
                    'error':str(e)},status=status.HTTP_400_BAD_REQUEST)
    

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            print("instance",instance)
            if instance:
                instance.delete()
            return Response({'status': True, 'message': 'Family deleted successfully'}, status=status.HTTP_200_OK)
        except Http404:
            return Response({'status': False, 'message': "Family not found!"},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'status':False,
                    'message':Global_error_message,
                    'error':str(e)},status=status.HTTP_400_BAD_REQUEST)
            
            


 # org_name = request.data.get('org_name')
            # if family.objects.filter(user=instance.user).exclude(id=instance.id).exists():
            #     return Response({"status":False, "message":" Family mail is already exists."}, status=status.HTTP_400_BAD_REQUEST)
            
# def list_page(self, request, *args, **kwargs):
    #     queryset = self.filter_queryset(self.get_queryset())

    #     ordering = request.query_params.get('ordering', None)
    #     if ordering:
    #         queryset = queryset.order_by(ordering)
    #     else:
    #         queryset = queryset.annotate(last_modified=Coalesce('updated_at', 'created_at')).order_by('-last_modified')    
    #     try:
    #         if not queryset.exists():
    #             return Response({"status": False, "message": "Data not found!", 'data': []}, status=status.HTTP_204_NO_CONTENT)
            
    #         page = self.paginate_queryset(queryset)
    #         if page is not None:
    #             serializer = self.serializer_class(page, many=True, context={'request': request})
    #             serializer = self.get_paginated_response(serializer.data)
    #         else:
    #             serializer = self.serializer_class(queryset, many=True, context={'request': request})

    #         count = serializer.data['count']
    #         limit = int(request.GET.get('page_size', 10))
    #         current_page = int(request.GET.get('page', 1))
    #         return Response({
    #             "status": True, 
    #             "message":"family Data.",
    #             'total_page': (count + limit - 1) // limit,
    #             'count': count,
    #             'current_page':current_page,
    #             'data': serializer.data['results']
    #         }, status=status.HTTP_200_OK)
        
    #     except Exception as e:
    #         return Response({
    #             'status': False,
    #             'message': "Something went wrong!",
    #             'error': str(e)
    #         }, status=status.HTTP_400_BAD_REQUEST)
            