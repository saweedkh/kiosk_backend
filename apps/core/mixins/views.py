from apps.logs.services.log_service import LogService


class LoggingMixin:
    def perform_create(self, serializer):
        instance = serializer.save()
        LogService.log_info(
            log_type='admin_action',
            action=f'{self.__class__.__name__}_create',
            user=self.request.user if hasattr(self, 'request') and self.request.user.is_authenticated else None,
            details={'instance_id': instance.id, 'model': instance.__class__.__name__}
        )
        return instance
    
    def perform_update(self, serializer):
        instance = serializer.save()
        LogService.log_info(
            log_type='admin_action',
            action=f'{self.__class__.__name__}_update',
            user=self.request.user if hasattr(self, 'request') and self.request.user.is_authenticated else None,
            details={'instance_id': instance.id, 'model': instance.__class__.__name__}
        )
        return instance
    
    def perform_destroy(self, instance):
        instance_id = instance.id
        model_name = instance.__class__.__name__
        instance.delete()
        LogService.log_info(
            log_type='admin_action',
            action=f'{self.__class__.__name__}_delete',
            user=self.request.user if hasattr(self, 'request') and self.request.user.is_authenticated else None,
            details={'instance_id': instance_id, 'model': model_name}
        )

