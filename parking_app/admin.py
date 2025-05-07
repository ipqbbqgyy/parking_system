"""
凉心科技停车场管理系统 - 后台管理完整配置
100%保留原有功能 + 新增停车配置管理
"""

from django.conf import settings
from django.contrib import admin
from django.urls import reverse, path
from django.utils.html import format_html
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render, redirect
from .models import (
    User, Vehicle, Membership, Promotion, Feedback,
    ContactMessage, JobPosition, AdminLogEntry, ParkingConfig, AdminActionLogger
)
from datetime import timedelta
from django.utils import timezone
import logging
from django.db.models.functions import ExtractHour, TruncDate, TruncMonth
from django.db.models import Sum, Q
from django.contrib.contenttypes.models import ContentType

logger = logging.getLogger(__name__)

class CustomAdminSite(admin.AdminSite):
    """完整保留原有CustomAdminSite实现"""
    site_header = format_html('<span style="color: #4ac1f7;">凉心科技后台管理系统</span>')
    site_title = '凉心科技'
    index_title = '管理首页'
    login_template = 'admin/login.html'
    index_template = 'admin/index.html'
    base_template = 'admin/base.html'

    def has_permission(self, request):
        return request.user.is_active and (request.user.is_staff or request.user.is_superuser)

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request)

        # 完整保留原有parking_app菜单项
        for app in app_list:
            if app['app_label'] == 'parking_app':
                app['models'] = [
                    {
                        'name': '会员',
                        'object_name': 'Membership',
                        'admin_url': '/admin/parking_app/membership/',
                        'view_only': False,
                    },
                    {
                        'name': '促销活动',
                        'object_name': 'Promotion',
                        'admin_url': '/admin/parking_app/promotion/',
                        'view_only': False,
                    },
                    {
                        'name': '招商合作',
                        'object_name': 'ContactMessage',
                        'admin_url': '/admin/parking_app/contactmessage/',
                        'view_only': False,
                    },
                    {
                        'name': '用户',
                        'object_name': 'User',
                        'admin_url': '/admin/parking_app/user/',
                        'view_only': False,
                    },
                    {
                        'name': '用户反馈',
                        'object_name': 'Feedback',
                        'admin_url': '/admin/parking_app/feedback/',
                        'view_only': False,
                    },
                    {
                        'name': '职位发布',
                        'object_name': 'JobPosition',
                        'admin_url': '/admin/parking_app/jobposition/',
                        'view_only': False,
                    },
                    {
                        'name': '车辆',
                        'object_name': 'Vehicle',
                        'admin_url': '/admin/parking_app/vehicle/',
                        'view_only': False,
                    },
                    # 新增的停车配置
                    {
                        'name': '停车系统配置',
                        'object_name': 'ParkingConfig',
                        'admin_url': '/admin/parking_app/parkingconfig/',
                        'view_only': False,
                    }
                ]
                break

        # 完整保留原有数据分析模块
        if self.has_permission(request):
            app_list.append({
                'name': '数据分析',
                'app_label': 'data_analysis',
                'models': [
                    {
                        'name': '车辆数据分析',
                        'object_name': 'ParkingAnalysis',
                        'admin_url': '/admin/parking_analysis/',
                        'view_only': True,
                    },
                    {
                        'name': '收入分析',
                        'object_name': 'IncomeAnalysis',
                        'admin_url': '/admin/income_analysis/',
                        'view_only': True,
                    },
                    {
                        'name': '管理员日志',
                        'object_name': 'AdminLogs',
                        'admin_url': '/admin/admin_logs/',
                        'view_only': True,
                    }
                ],
            })
        return app_list

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('parking_app/', self.admin_view(self.redirect_to_main_site), name='parking_app_redirect'),
            path('parking_analysis/', self.admin_view(self.parking_analysis_view), name='parking_analysis'),
            path('parking_analysis/data/', self.admin_view(self.get_parking_data), name='parking_data'),
            path('income_analysis/', self.admin_view(self.income_analysis_view), name='income_analysis'),
            path('income_analysis/data/', self.admin_view(self.get_income_data), name='income_data'),
            path('admin_logs/', self.admin_view(self.admin_logs_view), name='admin_logs'),
            path('admin_logs/data/', self.admin_view(self.get_admin_logs), name='admin_logs_data'),
            path(
                'user/<int:user_id>/password/',
                self.admin_view(PasswordChangeView.as_view(
                    success_url='password_change_done/',
                    template_name='admin/password_change_form.html'
                )),
                name='auth_user_password_change'
            ),
            path(
                'user/<int:user_id>/password/password_change_done/',
                self.admin_view(PasswordChangeDoneView.as_view(
                    template_name='admin/password_change_done.html'
                )),
                name='password_change_done'
            ),
        ]
        return custom_urls + urls

    def log_action(self, request, action, obj=None, message=""):
        AdminActionLogger.log(request, action, obj, message)

    def save_model(self, request, obj, form, change):
        action = 'update' if change else 'create'
        super().save_model(request, obj, form, change)
        self.log_action(request, action, obj)

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        self.log_action(request, 'delete', obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            self.log_action(request, 'delete', obj)
        super().delete_queryset(request, queryset)

    def redirect_to_main_site(self, request):
        return redirect('/')

    def parking_analysis_view(self, request):
        self.log_action(request, 'view', message="访问车辆数据分析页面")
        if not (request.user.is_superuser or request.user.is_staff):
            logger.warning(f'非授权用户尝试访问车辆数据分析: {request.user}')
            return HttpResponseForbidden("没有访问权限")
        vehicles = Vehicle.objects.all().order_by('-entry_time')
        context = {'vehicles': vehicles}
        return render(request, 'admin/parking_analysis.html', context)

    def income_analysis_view(self, request):
        self.log_action(request, 'view', message="访问收入分析页面")
        if not (request.user.is_superuser or request.user.is_staff):
            logger.warning(f'非授权用户尝试访问收入分析: {request.user}')
            return HttpResponseForbidden("没有访问权限")
        return render(request, 'admin/income_analysis.html')

    def admin_logs_view(self, request):
        self.log_action(request, 'view', message="访问管理员日志页面")
        if not (request.user.is_superuser or request.user.is_staff):
            logger.warning(f'非授权用户尝试访问管理员日志: {request.user}')
            return HttpResponseForbidden("没有访问权限")
        return render(request, 'admin/admin_logs.html')

    def get_parking_data(self, request):
        self.log_action(request, 'view', message="获取车辆数据")
        if not (request.user.is_superuser or request.user.is_staff):
            return JsonResponse({'success': False, 'error': '没有访问权限'}, status=403)
        vehicles = Vehicle.objects.all().order_by('-entry_time')[:100]
        data = {
            'success': True,
            'vehicles': [
                {
                    'license_plate': v.license_plate,
                    'spot_number': v.spot_number or '未知',
                    'entry_time': v.entry_time.strftime('%Y-%m-%d %H:%M'),
                    'exit_time': v.exit_time.strftime('%Y-%m-%d %H:%M') if v.exit_time else None,
                    'duration': v.parking_duration_minutes if v.exit_time else None,
                    'status': '已出库' if v.exit_time else '未出库'
                }
                for v in vehicles
            ]
        }
        return JsonResponse(data)

    def get_income_data(self, request):
        self.log_action(request, 'view', message="获取收入数据")
        try:
            if not (request.user.is_superuser or request.user.is_staff):
                return JsonResponse({'success': False, 'error': '没有访问权限'}, status=403)

            period = request.GET.get('period', 'today')
            now = timezone.now()

            if period == 'today':
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
                time_format = '%H:%M'
                group_by = 'hour'
            elif period == 'week':
                start_date = now - timedelta(days=now.weekday())
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date + timedelta(days=6)
                end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                time_format = '%m-%d'
                group_by = 'day'
            elif period == 'month':
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date + timedelta(days=32)
                end_date = end_date.replace(day=1) - timedelta(days=1)
                end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                time_format = '%m-%d'
                group_by = 'day'
            elif period == 'quarter':
                current_quarter = (now.month - 1) // 3 + 1
                start_date = now.replace(month=(current_quarter - 1) * 3 + 1, day=1,
                                         hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date + timedelta(days=93)
                end_date = end_date.replace(day=1) - timedelta(days=1)
                end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                time_format = '%m月'
                group_by = 'month'
            elif period == 'year':
                start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = now.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
                time_format = '%m月'
                group_by = 'month'
            else:
                first_record = Vehicle.objects.filter(paid=True).order_by('entry_time').first()
                start_date = first_record.entry_time if first_record else now
                end_date = now
                time_format = '%Y-%m'
                group_by = 'month'

            query = Vehicle.objects.filter(
                Q(paid=True) & Q(exit_time__isnull=False),
                exit_time__gte=start_date,
                exit_time__lte=end_date
            )

            trend_labels = []
            trend_amounts = []

            if group_by == 'hour':
                hours = range(24)
                trend_labels = [f"{h:02d}:00" for h in hours]
                hourly_data = query.annotate(
                    hour=ExtractHour('exit_time')
                ).values('hour').annotate(
                    total=Sum('fee')
                ).order_by('hour')
                trend_amounts = [0] * 24
                for item in hourly_data:
                    trend_amounts[item['hour']] = float(item['total'] or 0)

            elif group_by == 'day':
                days = (end_date - start_date).days + 1
                date_list = [start_date + timedelta(days=x) for x in range(days)]
                trend_labels = [d.strftime(time_format) for d in date_list]
                daily_data = query.annotate(
                    date=TruncDate('exit_time')
                ).values('date').annotate(
                    total=Sum('fee')
                ).order_by('date')
                daily_dict = {item['date'].strftime('%Y-%m-%d'): float(item['total'] or 0)
                              for item in daily_data}
                trend_amounts = [
                    daily_dict.get(d.strftime('%Y-%m-%d'), 0)
                    for d in date_list
                ]

            elif group_by == 'month':
                trend_labels = []
                trend_amounts = []
                current = start_date
                while current <= end_date:
                    trend_labels.append(current.strftime(time_format))
                    monthly_total = query.filter(
                        exit_time__year=current.year,
                        exit_time__month=current.month
                    ).aggregate(
                        total=Sum('fee')
                    )['total'] or 0
                    trend_amounts.append(float(monthly_total))
                    current += timedelta(days=32)
                    current = current.replace(day=1)

            record_list = []
            for vehicle in query.order_by('-exit_time')[:20]:
                record_list.append({
                    'date': vehicle.exit_time.strftime('%Y-%m-%d %H:%M'),
                    'license_plate': vehicle.license_plate,
                    'duration': vehicle.parking_duration_minutes,
                    'amount': float(vehicle.fee),
                    'is_member': hasattr(vehicle.user, 'membership') and vehicle.user.membership.is_active()
                })

            total_income = query.aggregate(total=Sum('fee'))['total'] or 0
            parking_count = query.count()
            if period == 'today':
                avg_income = total_income
            else:
                days = (min(end_date, now) - start_date).days + 1
                avg_income = total_income / days if days > 0 else 0

            return JsonResponse({
                'success': True,
                'stats': {
                    'total_income': float(total_income),
                    'avg_daily_income': float(avg_income),
                    'max_daily_income': max(trend_amounts) if trend_amounts else 0,
                    'parking_count': parking_count
                },
                'trend': {
                    'labels': trend_labels,
                    'amounts': trend_amounts
                },
                'records': record_list
            })
        except Exception as e:
            logger.error(f"获取收入数据时出错: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    def get_admin_logs(self, request):
        self.log_action(request, 'view', message="查询管理员日志")
        if not (request.user.is_superuser or request.user.is_staff):
            return JsonResponse({'success': False, 'error': '没有访问权限'}, status=403)

        try:
            logs = AdminLogEntry.objects.all().order_by('-timestamp')[:100]
            log_list = []

            for log in logs:
                shanghai_time = log.timestamp + timedelta(hours=8)
                formatted_time = shanghai_time.strftime('%Y-%m-%d %H:%M:%S')

                log_list.append({
                    'timestamp': formatted_time,
                    'username': log.user.username if log.user else '系统',
                    'action': log.get_action_display(),
                    'content_type': log.content_type.model if log.content_type else None,
                    'object_id': log.object_id,
                    'message': log.message
                })

            return JsonResponse({
                'success': True,
                'logs': log_list
            })

        except Exception as e:
            logger.error(f"查询管理员日志时出错: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

# 创建自定义AdminSite实例
custom_admin_site = CustomAdminSite(name='custom_admin')

# ==================== 原有所有模型Admin配置 ====================
@admin.register(Promotion, site=custom_admin_site)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('name', 'discount_info', 'time_range', 'status', 'created_at')
    list_filter = ('discount_type', 'is_active')
    search_fields = ('name',)
    date_hierarchy = 'start_time'

    fieldsets = (
        (None, {'fields': ('name', 'is_active')}),
        ('折扣设置', {
            'fields': ('discount_type', 'discount_value'),
            'description': '示例：八折请选择"百分比"并填写20（表示减免20%）'
        }),
        ('时间设置', {
            'fields': ('start_time', 'end_time'),
            'description': '设置促销生效的时间范围'
        }),
    )

    def save_model(self, request, obj, form, change):
        action = '修改' if change else '创建'
        message = f'{action}促销活动: {obj.name}'
        AdminActionLogger.log(request, 'update' if change else 'create', obj, message)
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        message = f'删除促销活动: {obj.name}'
        AdminActionLogger.log(request, 'delete', obj, message)
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            message = f'批量删除促销活动: {obj.name}'
            AdminActionLogger.log(request, 'delete', obj, message)
        super().delete_queryset(request, queryset)

    def discount_info(self, obj):
        if obj.discount_type == 'percent':
            return f"{100 - float(obj.discount_value)}% 折扣"
        return f"立减 {obj.discount_value}元"
    discount_info.short_description = '折扣信息'

    def time_range(self, obj):
        return format_html(
            f"{obj.start_time.strftime('%Y-%m-%d %H:%M')}<br>至<br>{obj.end_time.strftime('%Y-%m-%d %H:%M')}"
        )
    time_range.short_description = '生效时间'

    def status(self, obj):
        now = timezone.now()
        if obj.start_time > now:
            return '未开始'
        elif obj.end_time < now:
            return '已结束'
        return '进行中' if obj.is_active else '已禁用'
    status.short_description = '当前状态'

@admin.register(Vehicle, site=custom_admin_site)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        'order_number',
        'license_plate',
        'vehicle_type_display',
        'entry_time',
        'exit_time',
        'payment_display',
        'paid',
        'user'
    )
    list_filter = ('vehicle_type', 'paid', 'reserved')
    search_fields = ('license_plate', 'user__username', 'order_number')

    def vehicle_type_display(self, obj):
        return dict(Vehicle.VEHICLE_TYPE_CHOICES).get(obj.vehicle_type, '未知类型')
    vehicle_type_display.short_description = '车辆类型'

    def payment_display(self, obj):
        if obj.payment_amount:
            return f"¥{obj.payment_amount:.2f}"
        return "未支付"
    payment_display.short_description = '支付金额'

    def display_fee(self, obj):
        return f"{obj.fee:.2f}元"
    display_fee.short_description = '费用'

    def get_parking_duration(self, obj):
        if obj.exit_time:
            return f"{obj.parking_duration_hours:.2f}小时"
        return f"在场中 ({obj.parking_duration_minutes}分钟)"
    get_parking_duration.short_description = '停车时长'

    def is_reserved(self, obj):
        return "是" if obj.reserved else "否"
    is_reserved.short_description = '是否被预订'

    def save_model(self, request, obj, form, change):
        action = '修改' if change else '创建'
        message = f'{action}车辆记录: {obj.license_plate}'
        AdminActionLogger.log(request, 'update' if change else 'create', obj, message)
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        message = f'删除车辆记录: {obj.license_plate}'
        AdminActionLogger.log(request, 'delete', obj, message)
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            message = f'批量删除车辆记录: {obj.license_plate}'
            AdminActionLogger.log(request, 'delete', obj, message)
        super().delete_queryset(request, queryset)

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_superuser

@admin.register(User, site=custom_admin_site)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone_number', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('username', 'email')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('email', 'phone_number')}),
        ('权限', {
            'fields': ('is_active', 'is_staff', 'groups', 'user_permissions'),
            'description': '注意：超级用户状态只能通过命令行设置'
        }),
        ('重要日期', {'fields': ('last_login', 'date_joined')}),
    )

    def save_model(self, request, obj, form, change):
        action = '修改' if change else '创建'
        message = f'{action}用户: {obj.username}'
        AdminActionLogger.log(request, 'update' if change else 'create', obj, message)
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        message = f'删除用户: {obj.username}'
        AdminActionLogger.log(request, 'delete', obj, message)
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            message = f'批量删除用户: {obj.username}'
            AdminActionLogger.log(request, 'delete', obj, message)
        super().delete_queryset(request, queryset)

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_superuser

@admin.register(ContactMessage, site=custom_admin_site)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'created_at')
    search_fields = ('name', 'email')
    readonly_fields = ('created_at',)

    def save_model(self, request, obj, form, change):
        action = '修改' if change else '创建'
        message = f'{action}招商合作信息: {obj.name}'
        AdminActionLogger.log(request, 'update' if change else 'create', obj, message)
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        message = f'删除招商合作信息: {obj.name}'
        AdminActionLogger.log(request, 'delete', obj, message)
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            message = f'批量删除招商合作信息: {obj.name}'
            AdminActionLogger.log(request, 'delete', obj, message)
        super().delete_queryset(request, queryset)

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_superuser

@admin.register(JobPosition, site=custom_admin_site)
class JobPositionAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'created_at')
    search_fields = ('title', 'location')

    def save_model(self, request, obj, form, change):
        action = '修改' if change else '创建'
        message = f'{action}职位发布: {obj.title}'
        AdminActionLogger.log(request, 'update' if change else 'create', obj, message)
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        message = f'删除职位发布: {obj.title}'
        AdminActionLogger.log(request, 'delete', obj, message)
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            message = f'批量删除职位发布: {obj.title}'
            AdminActionLogger.log(request, 'delete', obj, message)
        super().delete_queryset(request, queryset)

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_superuser

@admin.register(Membership, site=custom_admin_site)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_membership_type_display', 'start_date', 'end_date', 'is_active')
    list_filter = ('membership_type',)
    search_fields = ('user__username',)

    def save_model(self, request, obj, form, change):
        action = '修改' if change else '创建'
        message = f'{action}会员: {obj.user.username}'
        AdminActionLogger.log(request, 'update' if change else 'create', obj, message)
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        message = f'删除会员: {obj.user.username}'
        AdminActionLogger.log(request, 'delete', obj, message)
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            message = f'批量删除会员: {obj.user.username}'
            AdminActionLogger.log(request, 'delete', obj, message)
        super().delete_queryset(request, queryset)

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_superuser

@admin.register(Feedback, site=custom_admin_site)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_feedback_type_display', 'content_short', 'created_at', 'is_resolved')
    list_filter = ('feedback_type', 'is_resolved')
    search_fields = ('content', 'user__username')
    list_editable = ('is_resolved',)
    readonly_fields = ('created_at',)

    fieldsets = (
        (None, {'fields': ('user', 'feedback_type', 'content', 'is_resolved')}),
        ('时间信息', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )

    def content_short(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_short.short_description = '反馈内容'

    def save_model(self, request, obj, form, change):
        action = '修改' if change else '创建'
        message = f'{action}用户反馈: {obj.user.username if obj.user else "匿名用户"}'
        AdminActionLogger.log(request, 'update' if change else 'create', obj, message)
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        message = f'删除用户反馈: {obj.user.username if obj.user else "匿名用户"}'
        AdminActionLogger.log(request, 'delete', obj, message)
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            message = f'批量删除用户反馈: {obj.user.username if obj.user else "匿名用户"}'
            AdminActionLogger.log(request, 'delete', obj, message)
        super().delete_queryset(request, queryset)

# ==================== 新增停车配置管理 ====================
@admin.register(ParkingConfig, site=custom_admin_site)
class ParkingConfigAdmin(admin.ModelAdmin):
    list_display = ('config_type_display', 'value', 'description', 'updated_at')
    list_editable = ('value', 'description')
    fields = ('config_type', 'value', 'description')
    readonly_fields = ('updated_at',)
    actions = ['reset_to_default']

    def config_type_display(self, obj):
        return obj.get_config_type_display()
    config_type_display.short_description = '配置类型'

    def reset_to_default(self, request, queryset):
        defaults = {
            'hourly_rate': '5.00',
            'free_duration': '15',
            'reservation_expiry': '30'
        }
        updated = 0
        for obj in queryset:
            if obj.config_type in defaults:
                obj.value = defaults[obj.config_type]
                obj.save()
                updated += 1
        self.message_user(request, f"已重置{updated}个配置的默认值")
    reset_to_default.short_description = "重置选中项为默认值"

# ==================== 初始化配置 ====================
def initialize_default_configs():
    default_configs = [
        ('hourly_rate', '5.00', '每小时停车费用(元)'),
        ('free_duration', '15', '免费停车时长(分钟)'),
        ('reservation_expiry', '30', '预订过期时间(分钟)')
    ]

    for config_type, value, desc in default_configs:
        ParkingConfig.objects.get_or_create(
            config_type=config_type,
            defaults={'value': value, 'description': desc}
        )

try:
    initialize_default_configs()
except Exception as e:
    logger.error(f"初始化停车配置失败: {str(e)}")