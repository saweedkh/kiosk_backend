from django.urls import path
from apps.admin_panel.api.reports.reports_apis import (
    SalesReportAPIView,
    TransactionReportAPIView,
    ProductReportAPIView,
    StockReportAPIView,
    DailyReportAPIView
)

urlpatterns = [
    path('sales/', SalesReportAPIView.as_view(), name='report-sales'),
    path('transactions/', TransactionReportAPIView.as_view(), name='report-transactions'),
    path('products/', ProductReportAPIView.as_view(), name='report-products'),
    path('stock/', StockReportAPIView.as_view(), name='report-stock'),
    path('daily/', DailyReportAPIView.as_view(), name='report-daily'),
]

