from django.utils import timezone
from datetime import timedelta
from apps.admin_panel.selectors.report_selector import ReportSelector
from apps.logs.services.log_service import LogService


class ReportService:
    @staticmethod
    def get_sales_report(start_date=None, end_date=None, user=None):
        report = ReportSelector.get_sales_report(start_date, end_date)
        
        LogService.log_info(
            'admin',
            'sales_report_generated',
            user=user,
            details={
                'start_date': str(start_date) if start_date else None,
                'end_date': str(end_date) if end_date else None
            }
        )
        
        return report
    
    @staticmethod
    def get_transaction_report(start_date=None, end_date=None, user=None):
        report = ReportSelector.get_transaction_report(start_date, end_date)
        
        LogService.log_info(
            'admin',
            'transaction_report_generated',
            user=user,
            details={
                'start_date': str(start_date) if start_date else None,
                'end_date': str(end_date) if end_date else None
            }
        )
        
        return report
    
    @staticmethod
    def get_product_report(user=None):
        report = {
            'products': list(ReportSelector.get_product_report())
        }
        
        LogService.log_info(
            'admin',
            'product_report_generated',
            user=user
        )
        
        return report
    
    @staticmethod
    def get_stock_report(user=None):
        report = ReportSelector.get_stock_report()
        
        LogService.log_info(
            'admin',
            'stock_report_generated',
            user=user
        )
        
        return report
    
    @staticmethod
    def get_daily_report(date=None, user=None):
        report = ReportSelector.get_daily_report(date)
        
        LogService.log_info(
            'admin',
            'daily_report_generated',
            user=user,
            details={'date': str(date) if date else None}
        )
        
        return report

