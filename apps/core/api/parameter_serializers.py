from rest_framework import serializers
from django.utils.translation import gettext_lazy as _


class BaseQuerySerializer(serializers.Serializer):
    """
    Base serializer for query parameters.
    
    All query parameter serializers should inherit from this class.
    """
    pass


class BasePathSerializer(serializers.Serializer):
    """
    Base serializer for path parameters.
    
    All path parameter serializers should inherit from this class.
    """
    pass


class PaginationQuerySerializer(BaseQuerySerializer):
    """
    Standard pagination query parameters.
    """
    page = serializers.IntegerField(
        help_text=_('Page number'),
        required=False,
        default=1,
        min_value=1
    )
    page_size = serializers.IntegerField(
        help_text=_('Number of items per page'),
        required=False,
        default=20,
        min_value=1,
        max_value=100
    )


class ProductQuerySerializer(BaseQuerySerializer):
    """
    Query parameters for product listing and filtering.
    """
    category = serializers.IntegerField(
        help_text=_('Filter by category ID'),
        required=False
    )
    min_price = serializers.IntegerField(
        help_text=_('Minimum price in Rial'),
        required=False,
        min_value=0
    )
    max_price = serializers.IntegerField(
        help_text=_('Maximum price in Rial'),
        required=False,
        min_value=0
    )
    in_stock = serializers.BooleanField(
        help_text=_('Filter by stock availability'),
        required=False
    )
    is_active = serializers.BooleanField(
        help_text=_('Filter by active status'),
        required=False
    )


class ProductSearchQuerySerializer(BaseQuerySerializer):
    """
    Query parameters for product search.
    """
    q = serializers.CharField(
        help_text=_('Search query string'),
        required=True,
        min_length=1
    )


class ProductPathSerializer(BasePathSerializer):
    """
    Path parameters for product detail endpoints.
    """
    pk = serializers.IntegerField(
        help_text=_('Product ID'),
        required=True
    )


class CategoryPathSerializer(BasePathSerializer):
    """
    Path parameters for category endpoints.
    """
    pk = serializers.IntegerField(
        help_text=_('Category ID'),
        required=True
    )


class CartItemPathSerializer(BasePathSerializer):
    """
    Path parameters for cart item endpoints.
    """
    pk = serializers.IntegerField(
        help_text=_('Cart item ID'),
        required=True
    )


class OrderPathSerializer(BasePathSerializer):
    """
    Path parameters for order endpoints.
    """
    pk = serializers.IntegerField(
        help_text=_('Order ID'),
        required=True
    )


class InvoicePathSerializer(BasePathSerializer):
    """
    Path parameters for invoice endpoints.
    """
    pk = serializers.IntegerField(
        help_text=_('Invoice ID'),
        required=True
    )


class TransactionPathSerializer(BasePathSerializer):
    """
    Path parameters for transaction endpoints.
    """
    pk = serializers.IntegerField(
        help_text=_('Transaction ID'),
        required=True
    )


class TransactionQuerySerializer(BaseQuerySerializer):
    """
    Query parameters for transaction listing.
    """
    order_id = serializers.IntegerField(
        help_text=_('Filter by order ID'),
        required=False
    )
    status = serializers.ChoiceField(
        choices=['pending', 'success', 'failed'],
        help_text=_('Filter by transaction status'),
        required=False
    )
    gateway_name = serializers.CharField(
        help_text=_('Filter by payment gateway name'),
        required=False
    )


class DateRangeQuerySerializer(BaseQuerySerializer):
    """
    Query parameters for date range filtering.
    """
    start_date = serializers.DateField(
        help_text=_('Start date for filtering (YYYY-MM-DD)'),
        required=False
    )
    end_date = serializers.DateField(
        help_text=_('End date for filtering (YYYY-MM-DD)'),
        required=False
    )


class DailyReportQuerySerializer(BaseQuerySerializer):
    """
    Query parameters for daily report.
    """
    date = serializers.DateField(
        help_text=_('Date for report (YYYY-MM-DD). Defaults to today if not provided.'),
        required=False
    )


class OrderQuerySerializer(BaseQuerySerializer):
    """
    Query parameters for order listing.
    """
    order_number = serializers.CharField(
        help_text=_('Filter by order number'),
        required=False
    )
    status = serializers.ChoiceField(
        choices=['pending', 'processing', 'completed', 'cancelled', 'paid'],
        help_text=_('Filter by order status'),
        required=False
    )
    payment_status = serializers.ChoiceField(
        choices=['pending', 'processing', 'paid', 'failed'],
        help_text=_('Filter by payment status'),
        required=False
    )


class AdminProductQuerySerializer(BaseQuerySerializer):
    """
    Query parameters for admin product listing.
    """
    name = serializers.CharField(
        help_text=_('Filter by product name (contains)'),
        required=False
    )
    category = serializers.IntegerField(
        help_text=_('Filter by category ID'),
        required=False
    )
    price_min = serializers.IntegerField(
        help_text=_('Minimum price in Rial'),
        required=False,
        min_value=0
    )
    price_max = serializers.IntegerField(
        help_text=_('Maximum price in Rial'),
        required=False,
        min_value=0
    )
    is_active = serializers.BooleanField(
        help_text=_('Filter by active status'),
        required=False
    )
    is_in_stock = serializers.BooleanField(
        help_text=_('Filter by stock availability'),
        required=False
    )
    is_low_stock = serializers.BooleanField(
        help_text=_('Filter by low stock status'),
        required=False
    )


class AdminCategoryQuerySerializer(BaseQuerySerializer):
    """
    Query parameters for admin category listing.
    """
    name = serializers.CharField(
        help_text=_('Filter by category name (contains)'),
        required=False
    )
    parent = serializers.IntegerField(
        help_text=_('Filter by parent category ID'),
        required=False
    )
    is_active = serializers.BooleanField(
        help_text=_('Filter by active status'),
        required=False
    )


class AdminOrderQuerySerializer(BaseQuerySerializer):
    """
    Query parameters for admin order listing.
    """
    order_number = serializers.CharField(
        help_text=_('Filter by order number'),
        required=False
    )
    status = serializers.ChoiceField(
        choices=['pending', 'processing', 'completed', 'cancelled', 'paid'],
        help_text=_('Filter by order status'),
        required=False
    )
    payment_status = serializers.ChoiceField(
        choices=['pending', 'processing', 'paid', 'failed'],
        help_text=_('Filter by payment status'),
        required=False
    )
    amount_min = serializers.IntegerField(
        help_text=_('Minimum order amount in Rial'),
        required=False,
        min_value=0
    )
    amount_max = serializers.IntegerField(
        help_text=_('Maximum order amount in Rial'),
        required=False,
        min_value=0
    )


class LoginRequestSerializer(BaseQuerySerializer):
    """
    Request parameters for admin login.
    """
    username = serializers.CharField(
        help_text=_('Admin username'),
        required=True
    )
    password = serializers.CharField(
        help_text=_('Admin password'),
        required=True,
        write_only=True
    )

