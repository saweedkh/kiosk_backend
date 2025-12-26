from rest_framework import generics
from rest_framework.response import Response
from apps.admin_panel.api.reports.reports_serializers import DateRangeSerializer, DailyReportSerializer
from apps.admin_panel.api.permissions import IsAdminUser
from apps.admin_panel.services.report_service import ReportService


class SalesReportAPIView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = DateRangeSerializer
    
    def get(self, request):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        report = ReportService.get_sales_report(
            start_date=serializer.validated_data.get('start_date'),
            end_date=serializer.validated_data.get('end_date'),
            user=request.user
        )
        
        return Response(report)


class TransactionReportAPIView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = DateRangeSerializer
    
    def get(self, request):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        report = ReportService.get_transaction_report(
            start_date=serializer.validated_data.get('start_date'),
            end_date=serializer.validated_data.get('end_date'),
            user=request.user
        )
        
        return Response(report)


class ProductReportAPIView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        report = ReportService.get_product_report(user=request.user)
        return Response(report)


class StockReportAPIView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        report = ReportService.get_stock_report(user=request.user)
        return Response(report)


class DailyReportAPIView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = DailyReportSerializer
    
    def get(self, request):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        report = ReportService.get_daily_report(
            date=serializer.validated_data.get('date'),
            user=request.user
        )
        
        return Response(report)

