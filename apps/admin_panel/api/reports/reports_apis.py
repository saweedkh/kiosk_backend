from rest_framework import generics, status
from rest_framework.response import Response
from apps.admin_panel.api.reports.reports_serializers import (
    DateRangeSerializer,
    DailyReportSerializer,
    SalesReportResponseSerializer,
    TransactionReportResponseSerializer,
    ProductReportResponseSerializer,
    StockReportResponseSerializer,
    DailyReportResponseSerializer
)
from apps.admin_panel.api.permissions import IsAdminUser
from apps.admin_panel.services.report_service import ReportService
from apps.core.api.schema import custom_extend_schema
from apps.core.api.schema import ResponseStatusCodes


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
        response_serializer=SalesReportResponseSerializer,
        status_codes=[
            ResponseStatusCodes.OK,
            ResponseStatusCodes.UNAUTHORIZED,
            ResponseStatusCodes.FORBIDDEN,
        ],
        summary="Sales Report",
        description="Generate sales report with statistics including total sales, total orders, and average order value.",
        tags=["Admin - Reports"],
        operation_id="admin_reports_sales",
    )
    def get(self, request):
        """
        Generate sales report.
        
        Args:
            request: HTTP request object with optional date range
            
        Returns:
            Response: Sales report data
        """
        params_serializer = DateRangeSerializer(data=request.query_params)
        params_serializer.is_valid(raise_exception=True)
        params = params_serializer.validated_data
        
        report = ReportService.get_sales_report(
            start_date=params.get('start_date'),
            end_date=params.get('end_date'),
            user=request.user
        )
        
        return Response(
            data=SalesReportResponseSerializer(report).data,
            status=status.HTTP_200_OK
        )


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
        response_serializer=TransactionReportResponseSerializer,
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
        params_serializer = DateRangeSerializer(data=request.query_params)
        params_serializer.is_valid(raise_exception=True)
        params = params_serializer.validated_data
        
        report = ReportService.get_transaction_report(
            start_date=params.get('start_date'),
            end_date=params.get('end_date'),
            user=request.user
        )
        
        return Response(
            data=TransactionReportResponseSerializer(report).data,
            status=status.HTTP_200_OK
        )


class ProductReportAPIView(generics.GenericAPIView):
    """
    API endpoint for generating product report (Admin only).
    
    Returns product statistics including total products, active products, and low stock products.
    """
    permission_classes = [IsAdminUser]
    
    @custom_extend_schema(
        resource_name="ProductReport",
        response_serializer=ProductReportResponseSerializer,
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
        
        return Response(
            data=ProductReportResponseSerializer(report).data,
            status=status.HTTP_200_OK
        )


class StockReportAPIView(generics.GenericAPIView):
    """
    API endpoint for generating stock report (Admin only).
    
    Returns inventory statistics including stock levels and stock value.
    """
    permission_classes = [IsAdminUser]
    
    @custom_extend_schema(
        resource_name="StockReport",
        response_serializer=StockReportResponseSerializer,
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
        
        return Response(
            data=StockReportResponseSerializer(report).data,
            status=status.HTTP_200_OK
        )


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
        response_serializer=DailyReportResponseSerializer,
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
        params_serializer = DailyReportSerializer(data=request.query_params)
        params_serializer.is_valid(raise_exception=True)
        params = params_serializer.validated_data
        
        report = ReportService.get_daily_report(
            date=params.get('date'),
            user=request.user
        )
        
        return Response(
            data=DailyReportResponseSerializer(report).data,
            status=status.HTTP_200_OK
        )

