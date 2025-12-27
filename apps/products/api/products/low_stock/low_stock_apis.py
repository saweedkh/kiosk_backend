from rest_framework import generics
from rest_framework.response import Response
from apps.products.api.products.low_stock.low_stock_serializers import ProductLowStockSerializer
from apps.products.selectors.product_selector import ProductSelector
from apps.core.api.schema import custom_extend_schema
from apps.core.api.status_codes import ResponseStatusCodes


class ProductLowStockAPIView(generics.GenericAPIView):
    """
    API endpoint for listing products with low stock.
    
    Returns a list of products where stock_quantity <= low_stock_threshold.
    """
    serializer_class = ProductLowStockSerializer
    
    @custom_extend_schema(
        resource_name="ProductLowStock",
        response_serializer=ProductLowStockSerializer,
        status_codes=[
            ResponseStatusCodes.OK_ALL,
        ],
        summary="List Low Stock Products",
        description="Get a list of products with low stock (stock_quantity <= low_stock_threshold).",
        tags=["Products"],
        operation_id="products_low_stock",
    )
    def get(self, request):
        """
        Get products with low stock.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: List of products with low stock
        """
        products = ProductSelector.get_low_stock_products()
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

