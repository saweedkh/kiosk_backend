from rest_framework import generics, status
from rest_framework.response import Response
from apps.products.models import Product
from apps.admin_panel.api.products.products_serializers import (
    AdminProductSerializer,
    AdminProductListSerializer,
    UpdateStockSerializer
)
from apps.admin_panel.api.products.products_filters import AdminProductFilter
from apps.admin_panel.api.permissions import IsAdminUser
from apps.products.services.product_service import ProductService
from apps.products.services.stock_service import StockService


class AdminProductListAPIView(generics.ListCreateAPIView):
    queryset = Product.objects.select_related('category').all()
    permission_classes = [IsAdminUser]
    filterset_class = AdminProductFilter
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return AdminProductListSerializer
        return AdminProductSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = ProductService.create_product(serializer.validated_data)
        return Response(
            AdminProductSerializer(product).data,
            status=status.HTTP_201_CREATED
        )


class AdminProductRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.select_related('category').all()
    serializer_class = AdminProductSerializer
    permission_classes = [IsAdminUser]
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        product = ProductService.update_product(instance, serializer.validated_data)
        return Response(AdminProductSerializer(product).data)


class AdminProductUpdateStockAPIView(generics.GenericAPIView):
    queryset = Product.objects.all()
    serializer_class = UpdateStockSerializer
    permission_classes = [IsAdminUser]
    
    def put(self, request, pk):
        product = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        StockService.update_stock(
            product_id=product.id,
            new_quantity=serializer.validated_data['stock_quantity'],
            change_type='manual',
            admin_user=request.user,
            notes=serializer.validated_data.get('notes', '')
        )
        
        product.refresh_from_db()
        return Response(AdminProductSerializer(product).data)

