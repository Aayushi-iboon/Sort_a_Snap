
# from rest_framework import viewsets
# from groups.model.group import PhotoGroupImage
# from groups.serializers.fevorite_serializers import Fev_image_Serializer
# from rest_framework.permissions import IsAuthenticated  
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework import filters
# from django_filters.rest_framework import DjangoFilterBackend
# from face.function_call import StandardResultsSetPagination,check_required_fields
# from django.contrib.auth import get_user_model

# User = get_user_model()

# class FevoriteimageViewSet(viewsets.ModelViewSet):
#     queryset = favorite_images.objects.all()
    # serializer_class = Fev_image_Serializer
#     permission_classes = [IsAuthenticated]
#     filter_backends = [filters.SearchFilter,DjangoFilterBackend]
#     pagination_class = StandardResultsSetPagination
#     filterset_fields = ['favorite']
#     search_fields = ['favorite']

#     def list(self, request, *args, **kwargs):
#         queryset = self.filter_queryset(self.get_queryset())
#         try:
#             if not queryset.exists():
#                 return Response({
#                     "status": False,
#                     "message": "No favourite photos found!",
#                     'data': []
#                 }, status=status.HTTP_204_NO_CONTENT)
#             serializer = self.serializer_class(queryset, many=True)
#             return Response({
#                 "status": True,
#                 "message": "favourite photos retrieved successfully.",
#                 'data': {"user_data":serializer.data} 
#             }, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({
#                 'status': False,
#                 'message': "Something went wrong!",
#                 'error': str(e)
#             }, status=status.HTTP_400_BAD_REQUEST)
            
#     def create(self, request, *args, **kwargs):
#         required_fields = ["favorite", "fevorite_image"]
#         upload_photo_error_message = check_required_fields(required_fields, request.data)
        
#         if upload_photo_error_message:
#             return Response({"status": False, "message": upload_photo_error_message}, status=status.HTTP_400_BAD_REQUEST)
        
#         serializer = self.serializer_class(data=request.data, context={'request': request})
#         if serializer.is_valid(raise_exception=True):
#             validated_data = serializer.validated_data

#             # Extract relevant fields for duplicate check
#             favorite = validated_data.get("favorite")
#             fevorite_image = validated_data.get("fevorite_image")
#             group = validated_data.get("group")
#             user = request.user  # Assuming `user` is the authenticated user making the request

#             # Check if a duplicate entry exists
#             if favorite_images.objects.filter(favorite=favorite, fevorite_image=fevorite_image, group=group, user=user).exists():
#                 return Response({
#                     "status": False,
#                     "message": "Duplicate entry: This image is already marked as favorite for the specified group.",
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             # Handle favorite logic
#             if favorite and group:
#                 # Unmark other favorite images in the same group
#                 favorite_images.objects.filter(group=group, favorite=True).update(favorite=False)

#                 # Clear existing associations in PhotoGroupImage
#                 photo_group_images = PhotoGroupImage.objects.filter(fav_images__group=group)
#                 if photo_group_images.exists():
#                     photo_group_images.update(fav_images=None)
            
#             # Save the new instance using the serializer
#             instance = serializer.save()
            
#             headers = self.get_success_headers(serializer.data)
#             return Response({
#                 "status": True,
#                 "message": "Favorite image set successfully.",
#                 "data": serializer.data
#             }, status=status.HTTP_201_CREATED, headers=headers)
            
    
#     def update(self, request, *args, **kwargs):
#         required_fields = ["favorite", "group_photo_image"]
#         upload_photo_error_message = check_required_fields(required_fields, request.data)
        
#         if upload_photo_error_message:
#             return Response({"status": False, "message": upload_photo_error_message}, status=status.HTTP_400_BAD_REQUEST)

#         group_photo_image_id = request.data.get("group_photo_image")
#         favorite_status = request.data.get("favorite")

#         try:
#             photo_group_image = PhotoGroupImage.objects.get(id=group_photo_image_id)
#             # Fetch the related favorite image 
#             instance = photo_group_image.fav_images

#             if not instance:
#                 return Response({
#                     "status": False,
#                     "message": f"No favorite image associated with GroupPhotoImage ID {group_photo_image_id}."
#                 }, status=status.HTTP_404_NOT_FOUND)

#         except PhotoGroupImage.DoesNotExist:
#             return Response({
#                 "status": False,
#                 "message": f"GroupPhotoImage with ID {group_photo_image_id} does not exist."
#             }, status=status.HTTP_404_NOT_FOUND)

#         serializer = self.serializer_class(instance, data=request.data, partial=True, context={'request': request})
#         if serializer.is_valid(raise_exception=True):
#             validated_data = serializer.validated_data
#             group = validated_data.get("group")

#             if favorite_status:
#                 if group:
#                     # Unmark other favorite images in the same group
#                     favorite_images.objects.filter(group=group, favorite=True).update(favorite=False)

#                     # Clear existing associations in PhotoGroupImage
#                     PhotoGroupImage.objects.filter(fav_images__group=group).update(fav_images=None)

#             # Update and save the instance
#             serializer.save()

#             return Response({
#                 "status": True,
#                 "message": "Favorite image updated successfully.",
#                 "data": serializer.data
#             }, status=status.HTTP_200_OK)
        
#         return Response({
#             "status": False,
#             "message": "Failed to update favorite image.",
#             "errors": serializer.errors
#         }, status=status.HTTP_400_BAD_REQUEST)
    
    
#     def retrieve(self, request, *args, **kwargs):
#         try:
#             instance = self.get_object()
#             serializer = self.serializer_class(instance)
#             return Response({
#                 'status': True,
#                 'message': 'Sub Group data retrieved successfully.',
#                 'data': serializer.data
#             }, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({
#                 'status': False,
#                 'message': 'Group not found.',
#                 'error': str(e)
#             }, status=status.HTTP_400_BAD_REQUEST)


#     def destroy(self, request, *args, **kwargs):
#         try:
#             instance = self.get_object()
#             instance.delete()
#             return Response({
#                 'status': True,
#                 'message': 'Fevourite deleted successfully.'
#             }, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({
#                 'status': False,
#                 'message': 'Error deleting group.',
#                 'error': str(e)
#             }, status=status.HTTP_400_BAD_REQUEST)
            
    
#     def userwise_fev_list(self, request, *args, **kwargs):
#         user_id = request.query_params.get("user_id")
#         if not user_id:
#             return Response({
#                 "status": False,
#                 "message": "User ID is required."
#             }, status=status.HTTP_400_BAD_REQUEST)
        
#         user = User.objects.filter(id=user_id).first()
#         if not user:
#             return Response({
#                 "status": False,
#                 "message": "User not found."
#             }, status=status.HTTP_404_NOT_FOUND)
            
#         queryset = favorite_images.objects.filter(user=user, favorite=True)
#         try:
#             if not queryset.exists():
#                 return Response({
#                     "status": False,
#                     "message": "No favourite photos found!",
#                     'data': []
#                 }, status=status.HTTP_204_NO_CONTENT)
#             serializer = self.serializer_class(queryset, many=True)
#             return Response({
#                 "status": True,
#                 "message": "favourite photos retrieved successfully.",
#                 'data': {"favourite_photos":serializer.data} 
#             }, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({
#                 'status': False,
#                 'message': "Something went wrong!",
#                 'error': str(e)
#             }, status=status.HTTP_400_BAD_REQUEST)