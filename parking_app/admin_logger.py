# admin_logger.py
from django.contrib.contenttypes.models import ContentType
from .models import AdminLogEntry

class AdminActionLogger:
    @staticmethod
    def log(request, action, obj=None, message=""):
        try:
            content_type = ContentType.objects.get_for_model(obj) if obj else None
            AdminLogEntry.objects.create(
                user=request.user,
                action=action,
                content_type=content_type,
                object_id=obj.pk if obj else None,
                message=message or f"{action} {obj.__class__.__name__} #{obj.pk}"
            )
        except Exception as e:
            logger.error(f"记录管理员日志失败: {str(e)}", exc_info=True)