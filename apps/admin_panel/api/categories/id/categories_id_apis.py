from rest_framework import generics
from apps.products.models import Category
from apps.admin_panel.api.categories.categories_serializers import AdminCategorySerializer
from apps.admin_panel.api.permissions import IsAdminUser
from apps.core.api.schema import custom_extend_schema
from apps.core.api.parameter_serializers import CategoryPathSerializer
from apps.core.api.status_codes import ResponseStatusCodes


class AdminCategoryRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, and deleting a category (Admin only).
    
    GET: Retrieve category details
    PUT/PATCH: Update category
    DELETE: Delete category
    """
    queryset = Category.objects.select_related('parent').prefetch_related('children').all()
    serializer_class = AdminCategorySerializer
    permission_classes = [IsAdminUser]
    
    @custom_extend_schema(
        resource_name="AdminCategoryRetrieve",
        parameters=[CategoryPathSerializer],
        response_serializer=AdminCategorySerializer,
        status_codes=[
            ResponseStatusCodes.OK,
            ResponseStatusCodes.NOT_FOUND,
            ResponseStatusCodes.UNAUTHORIZED,
            ResponseStatusCodes.FORBIDDEN,
        ],
        summary="Get Category Details (Admin)",
        description="Retrieve detailed information about a category. Admin only.",
        tags=["Admin - Categories"],
        operation_id="admin_categories_retrieve",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @custom_extend_schema(
        resource_name="AdminCategoryUpdate",
        parameters=[CategoryPathSerializer, AdminCategorySerializer],
        request_serializer=AdminCategorySerializer,
        response_serializer=AdminCategorySerializer,
        status_codes=[
            ResponseStatusCodes.OK,
            ResponseStatusCodes.BAD_REQUEST,
            ResponseStatusCodes.NOT_FOUND,
            ResponseStatusCodes.UNAUTHORIZED,
            ResponseStatusCodes.FORBIDDEN,
        ],
        summary="Update Category (Admin)",
        description="Update category information (full update). Admin only.",
        tags=["Admin - Categories"],
        operation_id="admin_categories_update",
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @custom_extend_schema(
        resource_name="AdminCategoryPartialUpdate",
        parameters=[CategoryPathSerializer, AdminCategorySerializer],
        request_serializer=AdminCategorySerializer,
        response_serializer=AdminCategorySerializer,
        status_codes=[
            ResponseStatusCodes.OK,
            ResponseStatusCodes.BAD_REQUEST,
            ResponseStatusCodes.NOT_FOUND,
            ResponseStatusCodes.UNAUTHORIZED,
            ResponseStatusCodes.FORBIDDEN,
        ],
        summary="Partially Update Category (Admin)",
        description="Partially update category information. Admin only.",
        tags=["Admin - Categories"],
        operation_id="admin_categories_partial_update",
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @custom_extend_schema(
        resource_name="AdminCategoryDelete",
        parameters=[CategoryPathSerializer],
        status_codes=[
            ResponseStatusCodes.NO_CONTENT,
            ResponseStatusCodes.NOT_FOUND,
            ResponseStatusCodes.UNAUTHORIZED,
            ResponseStatusCodes.FORBIDDEN,
        ],
        summary="Delete Category (Admin)",
        description="Delete a category. Admin only.",
        tags=["Admin - Categories"],
        operation_id="admin_categories_delete",
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

