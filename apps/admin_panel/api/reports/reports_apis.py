from rest_framework import generics
from rest_framework.response import Response
from apps.admin_panel.api.reports.reports_serializers import DateRangeSerializer, DailyReportSerializer
from apps.admin_panel.api.permissions import IsAdminUser
from apps.admin_panel.services.report_service import ReportService
from apps.core.api.schema import custom_extend_schema
from apps.core.api.parameter_serializers import DateRangeQuerySerializer, DailyReportQuerySerializer
from apps.core.api.status_codes import ResponseStatusCodes


class SalesReportAPIView(generics.GenericAPIView):
    """
    API endpoint for generating sales report (Admin only).
    
    Query Parameters:
        start_date: Start date for report (optional)
        end_date: End date for report (optional)
        
    Returns sales statistics including total sales, total orders, and average order value.
    """
    permission_classes = [IsAdminUser]
    serializer_class = DateRangeSerializer
    
    @custom_extend_schema(
        resource_name="SalesReport",
        parameters=[DateRangeQuerySerializer],
        status_codes=[
            ResponseStatusCodes.OK,
            ResponseStatusCodes.UNAUTHORIZED,
            ResponseStatusCodes.FORBIDDEN,
        ],
        summary="Sales Report",
        description="Generate sales report with statistics including total sales, total orders, and average order value.",
        tags=["Admin - Reports"],
    )
    def get(self, request):
        """
        Generate sales report.
        
        Args:
            request: HTTP request object with optional date range
            
        Returns:
            Response: Sales report data
        """
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        report = ReportService.get_sales_report(
            start_date=serializer.validated_data.get('start_date'),
            end_date=serializer.validated_data.get('end_date'),
            user=request.user
        )
        
        return Response(report)


class TransactionReportAPIView(generics.GenericAPIView):
    """
    API endpoint for generating transaction report (Admin only).
    
    Query Parameters:
        start_date: Start date for report (optional)
        end_date: End date for report (optional)
        
    Returns payment transaction statistics including success/failure rates.
    """
    permission_classes = [IsAdminUser]
    serializer_class = DateRangeSerializer
    
    @custom_extend_schema(
        resource_name="TransactionReport",
        parameters=[DateRangeQuerySerializer],
        status_codes=[
            ResponseStatusCodes.OK,
            ResponseStatusCodes.UNAUTHORIZED,
            ResponseStatusCodes.FORBIDDEN,
        ],
        summary="Transaction Report",
        description="Generate payment transaction report with statistics including success/failure rates and total amounts.",
        tags=["Admin - Reports"],
        operation_id="admin_reports_transaction",
    )
    def get(self, request):
        """
        Generate transaction report.
        
        Args:
            request: HTTP request object with optional date range
            
        Returns:
            Response: Transaction report data
        """
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        report = ReportService.get_transaction_report(
            start_date=serializer.validated_data.get('start_date'),
            end_date=serializer.validated_data.get('end_date'),
            user=request.user
        )
        
        return Response(report)


class ProductReportAPIView(generics.GenericAPIView):
    """
    API endpoint for generating product report (Admin only).
    
    Returns product statistics including total products, active products, and low stock products.
    """
    permission_classes = [IsAdminUser]
    
    @custom_extend_schema(
        resource_name="ProductReport",
        status_codes=[
            ResponseStatusCodes.OK,
            ResponseStatusCodes.UNAUTHORIZED,
            ResponseStatusCodes.FORBIDDEN,
        ],
        summary="Product Report",
        description="Generate product report with statistics including total products, active products, and low stock products.",
        tags=["Admin - Reports"],
        operation_id="admin_reports_product",
    )
    def get(self, request):
        """
        Generate product report.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: Product report data
        """
        report = ReportService.get_product_report(user=request.user)
        return Response(report)


class StockReportAPIView(generics.GenericAPIView):
    """
    API endpoint for generating stock report (Admin only).
    
    Returns inventory statistics including stock levels and stock value.
    """
    permission_classes = [IsAdminUser]
    
    @custom_extend_schema(
        resource_name="StockReport",
        status_codes=[
            ResponseStatusCodes.OK,
            ResponseStatusCodes.UNAUTHORIZED,
            ResponseStatusCodes.FORBIDDEN,
        ],
        summary="Stock Report",
        description="Generate stock report with inventory statistics including stock levels and stock value.",
        tags=["Admin - Reports"],
        operation_id="admin_reports_stock",
    )
    def get(self, request):
        """
        Generate stock report.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: Stock report data
        """
        report = ReportService.get_stock_report(user=request.user)
        return Response(report)


class DailyReportAPIView(generics.GenericAPIView):
    """
    API endpoint for generating daily report (Admin only).
    
    Query Parameters:
        date: Date for report (optional, defaults to today)
        
    Returns daily statistics including sales, orders, and transactions for a specific date.
    """
    permission_classes = [IsAdminUser]
    serializer_class = DailyReportSerializer
    
    @custom_extend_schema(
        resource_name="DailyReport",
        parameters=[DailyReportQuerySerializer],
        status_codes=[
            ResponseStatusCodes.OK,
            ResponseStatusCodes.UNAUTHORIZED,
            ResponseStatusCodes.FORBIDDEN,
        ],
        summary="Daily Report",
        description="Generate daily report with statistics including sales, orders, and transactions for a specific date.",
        tags=["Admin - Reports"],
        operation_id="admin_reports_daily",
    )
    def get(self, request):
        """
        Generate daily report.
        
        Args:
            request: HTTP request object with optional date
            
        Returns:
            Response: Daily report data
        """
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        report = ReportService.get_daily_report(
            date=serializer.validated_data.get('date'),
            user=request.user
        )
        
        return Response(report)

