from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel
from .managers import CartManager


class Cart(TimeStampedModel):
    session_key = models.CharField(max_length=40, unique=True, verbose_name=_('کلید Session'))
    
    objects = CartManager()
    
    class Meta:
        verbose_name = _('سبد خرید')
        verbose_name_plural = _('سبدهای خرید')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Cart - {self.session_key[:8]}..."


class CartItem(TimeStampedModel):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('سبد خرید')
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        verbose_name=_('محصول')
    )
    quantity = models.IntegerField(default=1, verbose_name=_('تعداد'))
    unit_price = models.IntegerField(verbose_name=_('قیمت واحد'))
    
    class Meta:
        verbose_name = _('آیتم سبد خرید')
        verbose_name_plural = _('آیتم‌های سبد خرید')
        unique_together = ['cart', 'product']
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity}"
    
    @property
    def subtotal(self):
        return self.quantity * self.unit_price
