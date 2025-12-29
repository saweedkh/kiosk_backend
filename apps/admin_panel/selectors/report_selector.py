from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from datetime import timedelta, datetime
from apps.orders.models import Order, OrderItem
from apps.payment.models import Transaction
from apps.products.models import Product


class ReportSelector:
    @staticmethod
    def get_sales_report(start_date=None, end_date=None):
        queryset = Order.objects.all()
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        total_sales = queryset.aggregate(
            total_amount=Sum('total_amount'),
            total_orders=Count('id'),
            average_order=Avg('total_amount')
        )
        
        return {
            'total_sales': total_sales['total_amount'] or 0,
            'total_orders': total_sales['total_orders'] or 0,
            'average_order': total_sales['average_order'] or 0,
            'start_date': start_date,
            'end_date': end_date
        }
    
    @staticmethod
    def get_transaction_report(start_date=None, end_date=None):
        queryset = Transaction.objects.all()
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        successful = queryset.filter(status='success')
        failed = queryset.filter(status='failed')
        
        return {
            'total_transactions': queryset.count(),
            'successful_transactions': successful.count(),
            'failed_transactions': failed.count(),
            'total_amount': successful.aggregate(total=Sum('amount'))['total'] or 0,
            'start_date': start_date,
            'end_date': end_date
        }
    
    @staticmethod
    def get_product_report():
        products = Product.objects.annotate(
            total_sold=Sum(
                'orderitem__quantity',
                filter=Q(orderitem__order__status__in=['paid', 'completed'])
            )
        ).annotate(
            total_revenue=Sum(
                F('orderitem__quantity') * F('orderitem__unit_price'),
                filter=Q(orderitem__order__status__in=['paid', 'completed'])
            )
        )
        
        return products.values(
            'id', 'name', 'price', 'stock_quantity',
            'total_sold', 'total_revenue'
        )
    
    @staticmethod
    def get_stock_report():
        out_of_stock = Product.objects.filter(stock_quantity=0).count()
        total_products = Product.objects.count()
        
        return {
            'out_of_stock_count': out_of_stock,
            'total_products': total_products
        }
    
    @staticmethod
    def get_daily_report(date=None):
        if not date:
            date = timezone.now().date()
        
        start = timezone.make_aware(datetime.combine(date, datetime.min.time()))
        end = timezone.make_aware(datetime.combine(date, datetime.max.time()))
        
        orders = Order.objects.filter(created_at__range=[start, end])
        transactions = Transaction.objects.filter(created_at__range=[start, end])
        
        return {
            'date': date.isoformat(),
            'total_orders': orders.count(),
            'total_sales': orders.aggregate(total=Sum('total_amount'))['total'] or 0,
            'total_transactions': transactions.count(),
            'successful_transactions': transactions.filter(status='success').count(),
            'failed_transactions': transactions.filter(status='failed').count()
        }

