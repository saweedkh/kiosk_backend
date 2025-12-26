from rest_framework import serializers
from django.utils.translation import gettext_lazy as _


class DateRangeSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False, label=_('تاریخ شروع'))
    end_date = serializers.DateField(required=False, label=_('تاریخ پایان'))


class DailyReportSerializer(serializers.Serializer):
    date = serializers.DateField(required=False, label=_('تاریخ'))

