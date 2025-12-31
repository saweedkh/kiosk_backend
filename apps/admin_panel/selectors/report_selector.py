from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from datetime import timedelta, datetime
from apps.orders.models import Order, OrderItem
from apps.products.models import Product


class ReportSelector:
    @staticmethod
    def get_sales_report(start_date=None, end_date=None):
        queryset = Order.objects.all()
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        # محاسبه مجموع فروش و تعداد سفارشات
        total_sales = queryset.aggregate(
            total_amount=Sum('total_amount'),
            total_orders=Count('id')
        )
        
        # محاسبه میانگین به صورت جداگانه
        total_amount = total_sales['total_amount'] or 0
        total_orders = total_sales['total_orders'] or 0
        average_order_value = (total_amount / total_orders) if total_orders > 0 else 0
        
        # لیست سفارشات با فیلدهای کامل
        orders_list = list(queryset.values(
            'id', 'order_number', 'total_amount', 'status', 
            'payment_status', 'transaction_id', 'gateway_name',
            'payment_method', 'created_at', 'updated_at'
        ))
        
        return {
            'total_sales': total_amount,
            'total_orders': total_orders,
            'average_order_value': round(average_order_value, 2),
            'orders': orders_list,
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None
        }
    
    @staticmethod
    def get_transaction_report(start_date=None, end_date=None):
        # استفاده از Order به جای Transaction
        queryset = Order.objects.exclude(transaction_id__isnull=True).exclude(transaction_id='')
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        successful = queryset.filter(payment_status='paid')
        failed = queryset.filter(payment_status='failed')
        
        # لیست تراکنش‌ها (از Order) با فیلدهای کامل
        transactions_list = list(queryset.values(
            'id', 'order_number', 'transaction_id', 'total_amount', 
            'payment_status', 'gateway_name', 'payment_method',
            'error_message', 'created_at', 'updated_at'
        ))
        
        # تغییر نام فیلدها برای سازگاری با serializer
        for trans in transactions_list:
            trans['order_id'] = trans['id']
            trans['amount'] = trans['total_amount']
            trans['status'] = trans['payment_status']
        
        return {
            'total_transactions': queryset.count(),
            'successful_transactions': successful.count(),
            'failed_transactions': failed.count(),
            'total_amount': successful.aggregate(total=Sum('total_amount'))['total'] or 0,
            'transactions': transactions_list,
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None
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
        
        products_list = list(products.values(
            'id', 'name', 'description', 'price', 'stock_quantity', 'is_active',
            'category__name', 'total_sold', 'total_revenue'
        ))
        
        # تغییر نام فیلد category__name به category_name
        for product in products_list:
            product['category_name'] = product.pop('category__name', '')
        
        total_products = Product.objects.count()
        active_products = Product.objects.filter(is_active=True).count()
        
        return {
            'total_products': total_products,
            'active_products': active_products,
            'products': products_list
        }
    
    @staticmethod
    def get_stock_report():
        products = Product.objects.all()
        
        # محاسبه ارزش کل موجودی و تعداد کل آیتم‌ها با استفاده از aggregate
        stock_aggregate = products.aggregate(
            total_stock_value=Sum(F('stock_quantity') * F('price')),
            total_items=Sum('stock_quantity')
        )
        
        total_stock_value = stock_aggregate['total_stock_value'] or 0
        total_items = stock_aggregate['total_items'] or 0
        
        # جزئیات موجودی هر محصول
        stock_details = []
        for product in products:
            stock_value = product.stock_quantity * product.price
            min_stock = getattr(product, 'min_stock_level', 10)
            
            stock_details.append({
                'id': product.id,
                'name': product.name,
                'category_name': product.category.name if product.category else '',
                'stock_quantity': product.stock_quantity,
                'price': product.price,
                'stock_value': stock_value,
                'is_active': product.is_active,
                'is_low_stock': product.stock_quantity < min_stock,
                'is_out_of_stock': product.stock_quantity == 0
            })
        
        return {
            'total_stock_value': total_stock_value,
            'total_items': total_items,
            'stock_details': stock_details
        }
    
    @staticmethod
    def get_daily_report(date=None):
        if not date:
            date = timezone.now().date()
        
        start = timezone.make_aware(datetime.combine(date, datetime.min.time()))
        end = timezone.make_aware(datetime.combine(date, datetime.max.time()))
        
        orders = Order.objects.filter(created_at__range=[start, end])
        # استفاده از Order به جای Transaction
        transactions = Order.objects.filter(
            created_at__range=[start, end]
        ).exclude(transaction_id__isnull=True).exclude(transaction_id='')
        
        # لیست سفارشات با فیلدهای کامل
        orders_list = list(orders.values(
            'id', 'order_number', 'total_amount', 'status', 
            'payment_status', 'transaction_id', 'gateway_name',
            'payment_method', 'created_at', 'updated_at'
        ))
        
        return {
            'date': date.isoformat(),
            'total_orders': orders.count(),
            'total_sales': orders.aggregate(total=Sum('total_amount'))['total'] or 0,
            'total_transactions': transactions.count(),
            'orders': orders_list
        }

