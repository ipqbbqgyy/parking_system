"""
自定义Django Admin后台管理系统配置
包含车辆管理、用户管理、促销活动、管理员日志等功能
"""

from django.conf import settings
from django.contrib import admin
from django.urls import reverse, path
from django.utils.html import format_html
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render
from .models import Vehicle, User, ContactMessage, JobPosition, Membership, AdminLogEntry, Promotion, Feedback
from datetime import timedelta
from django.utils import timezone
import logging
from django.db.models.functions import ExtractHour, TruncDate, TruncMonth
from django.db.models import Sum, Q
from django.contrib.contenttypes.models import ContentType
from .models import AdminActionLogger

# 获取日志记录器
logger = logging.getLogger(__name__)


class CustomAdminSite(admin.AdminSite):
    """
    自定义AdminSite类，用于扩展默认的Django Admin功能
    """

    # 自定义后台界面标题和样式
    site_header = format_html('<span style="color: #4ac1f7;">凉心科技后台管理系统</span>')
    site_title = '凉心科技'
    index_title = '管理首页'

    # 自定义模板
    login_template = 'admin/login.html'
    index_template = 'admin/index.html'
    base_template = 'admin/base.html'

    def has_permission(self, request):
        """
        检查用户是否有访问后台的权限
        要求用户是活跃状态且是员工或超级用户
        """
        return request.user.is_active and (request.user.is_staff or request.user.is_superuser)

    def get_app_list(self, request, app_label=None):
        """
        自定义左侧导航菜单，添加数据分析模块
        """
        app_list = super().get_app_list(request)

        # 找到parking_app应用并添加用户反馈
        for app in app_list:
            if app['app_label'] == 'parking_app':
                app['models'].append({
                    'name': '用户反馈',
                    'object_name': 'Feedback',
                    'admin_url': '/admin/parking_app/feedback/',
                    'view_only': False,
                })
                break

        if self.has_permission(request):
            # 添加数据分析模块
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
        """
        添加自定义URL路由
        """
        urls = super().get_urls()
        custom_urls = [
            # 停车场应用重定向
            path('parking_app/', self.admin_view(self.redirect_to_main_site), name='parking_app_redirect'),
            # 车辆数据分析相关路由
            path('parking_analysis/', self.admin_view(self.parking_analysis_view), name='parking_analysis'),
            path('parking_analysis/data/', self.admin_view(self.get_parking_data), name='parking_data'),
            # 收入分析相关路由
            path('income_analysis/', self.admin_view(self.income_analysis_view), name='income_analysis'),
            path('income_analysis/data/', self.admin_view(self.get_income_data), name='income_data'),
            # 管理员日志相关路由
            path('admin_logs/', self.admin_view(self.admin_logs_view), name='admin_logs'),
            path('admin_logs/data/', self.admin_view(self.get_admin_logs), name='admin_logs_data'),
            # 密码修改相关路由
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
        """
        记录管理员操作日志的通用方法
        """
        AdminActionLogger.log(request, action, obj, message)

    def save_model(self, request, obj, form, change):
        """
        重写保存模型方法，记录操作日志
        """
        action = 'update' if change else 'create'
        super().save_model(request, obj, form, change)
        self.log_action(request, action, obj)

    def delete_model(self, request, obj):
        """
        重写删除模型方法，记录操作日志
        """
        super().delete_model(request, obj)
        self.log_action(request, 'delete', obj)

    def delete_queryset(self, request, queryset):
        """
        重写批量删除方法，记录操作日志
        """
        for obj in queryset:
            self.log_action(request, 'delete', obj)
        super().delete_queryset(request, queryset)

    def redirect_to_main_site(self, request):
        """
        重定向到主站点
        """
        from django.shortcuts import redirect
        return redirect('/')

    def parking_analysis_view(self, request):
        """
        车辆数据分析视图
        """
        self.log_action(request, 'view', message="访问车辆数据分析页面")
        if not (request.user.is_superuser or request.user.is_staff):
            logger.warning(f'非授权用户尝试访问车辆数据分析: {request.user}')
            return HttpResponseForbidden("没有访问权限")
        vehicles = Vehicle.objects.all().order_by('-entry_time')
        context = {'vehicles': vehicles}
        return render(request, 'admin/parking_analysis.html', context)

    def income_analysis_view(self, request):
        """
        收入分析视图
        """
        self.log_action(request, 'view', message="访问收入分析页面")
        if not (request.user.is_superuser or request.user.is_staff):
            logger.warning(f'非授权用户尝试访问收入分析: {request.user}')
            return HttpResponseForbidden("没有访问权限")
        return render(request, 'admin/income_analysis.html')

    def admin_logs_view(self, request):
        """
        管理员日志视图
        """
        self.log_action(request, 'view', message="访问管理员日志页面")
        if not (request.user.is_superuser or request.user.is_staff):
            logger.warning(f'非授权用户尝试访问管理员日志: {request.user}')
            return HttpResponseForbidden("没有访问权限")
        return render(request, 'admin/admin_logs.html')

    def get_parking_data(self, request):
        """
        获取车辆数据的API接口
        返回JSON格式的车辆数据
        """
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
        """
        获取收入数据的API接口
        支持按不同时间周期统计收入数据
        """
        self.log_action(request, 'view', message="获取收入数据")
        try:
            if not (request.user.is_superuser or request.user.is_staff):
                return JsonResponse({'success': False, 'error': '没有访问权限'}, status=403)

            # 获取请求的时间周期参数
            period = request.GET.get('period', 'today')
            now = timezone.now()

            # 根据不同的周期设置查询时间范围
            if period == 'today':  # 今天
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
                time_format = '%H:%M'
                group_by = 'hour'
            elif period == 'week':  # 本周
                start_date = now - timedelta(days=now.weekday())
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date + timedelta(days=6)
                end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                time_format = '%m-%d'
                group_by = 'day'
            elif period == 'month':  # 本月
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date + timedelta(days=32)
                end_date = end_date.replace(day=1) - timedelta(days=1)
                end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                time_format = '%m-%d'
                group_by = 'day'
            elif period == 'quarter':  # 本季度
                current_quarter = (now.month - 1) // 3 + 1
                start_date = now.replace(month=(current_quarter - 1) * 3 + 1, day=1,
                                         hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date + timedelta(days=93)
                end_date = end_date.replace(day=1) - timedelta(days=1)
                end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                time_format = '%m月'
                group_by = 'month'
            elif period == 'year':  # 本年
                start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = now.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
                time_format = '%m月'
                group_by = 'month'
            else:  # 全部
                first_record = Vehicle.objects.filter(paid=True).order_by('entry_time').first()
                start_date = first_record.entry_time if first_record else now
                end_date = now
                time_format = '%Y-%m'
                group_by = 'month'

            # 查询已支付且有出场时间的车辆记录
            query = Vehicle.objects.filter(
                Q(paid=True) & Q(exit_time__isnull=False),
                exit_time__gte=start_date,
                exit_time__lte=end_date
            )

            # 初始化趋势数据
            trend_labels = []
            trend_amounts = []

            # 按小时统计
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

            # 按天统计
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

            # 按月统计
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

            # 准备详细记录列表
            record_list = []
            for vehicle in query.order_by('-exit_time')[:20]:
                record_list.append({
                    'date': vehicle.exit_time.strftime('%Y-%m-%d %H:%M'),
                    'license_plate': vehicle.license_plate,
                    'duration': vehicle.parking_duration_minutes,
                    'amount': float(vehicle.fee),
                    'is_member': hasattr(vehicle.user, 'membership') and vehicle.user.membership.is_active()
                })

            # 计算统计指标
            total_income = query.aggregate(total=Sum('fee'))['total'] or 0
            parking_count = query.count()
            if period == 'today':
                avg_income = total_income
            else:
                days = (min(end_date, now) - start_date).days + 1
                avg_income = total_income / days if days > 0 else 0

            # 返回JSON响应
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
        """
        获取管理员日志的API接口
        返回JSON格式的管理员操作日志
        """
        self.log_action(request, 'view', message="查询管理员日志")
        if not (request.user.is_superuser or request.user.is_staff):
            return JsonResponse({'success': False, 'error': '没有访问权限'}, status=403)

        try:
            # 获取最新的100条日志记录
            logs = AdminLogEntry.objects.all().order_by('-timestamp')[:100]
            log_list = []

            for log in logs:
                # 转换为上海时间 (UTC+8)
                shanghai_time = log.timestamp + timedelta(hours=8)
                formatted_time = shanghai_time.strftime('%Y-%m-%d %H:%M:%S')

                # 构建日志条目
                log_list.append({
                    'timestamp': formatted_time,  # 格式化后的时间
                    'username': log.user.username if log.user else '系统',  # 操作用户
                    'action': log.get_action_display(),  # 操作类型(显示名称)
                    'content_type': log.content_type.model if log.content_type else None,  # 操作对象类型
                    'object_id': log.object_id,  # 操作对象ID
                    'message': log.message  # 操作详情
                })

            # 返回JSON响应
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


# ==================== 以下是各个模型的Admin配置 ====================

@admin.register(Promotion, site=custom_admin_site)
class PromotionAdmin(admin.ModelAdmin):
    """
    促销活动管理配置
    """
    list_display = ('name', 'discount_info', 'time_range', 'status', 'created_at')
    list_filter = ('discount_type', 'is_active')
    search_fields = ('name',)
    date_hierarchy = 'start_time'

    fieldsets = (
        (None, {
            'fields': ('name', 'is_active')
        }),
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
        """显示折扣信息"""
        if obj.discount_type == 'percent':
            return f"{100 - float(obj.discount_value)}% 折扣"
        return f"立减 {obj.discount_value}元"

    discount_info.short_description = '折扣信息'

    def time_range(self, obj):
        """显示时间范围"""
        return format_html(
            f"{obj.start_time.strftime('%Y-%m-%d %H:%M')}<br>至<br>{obj.end_time.strftime('%Y-%m-%d %H:%M')}"
        )

    time_range.short_description = '生效时间'

    def status(self, obj):
        """显示当前状态"""
        now = timezone.now()
        if obj.start_time > now:
            return '未开始'
        elif obj.end_time < now:
            return '已结束'
        return '进行中' if obj.is_active else '已禁用'

    status.short_description = '当前状态'


@admin.register(Vehicle, site=custom_admin_site)
class VehicleAdmin(admin.ModelAdmin):
    """
    车辆管理配置
    """
    list_display = (
        'order_number',  # 订单号（第一列显示）
        'license_plate',  # 车牌号
        'vehicle_type_display',  # 车辆类型（使用中文显示）
        'entry_time',  # 入场时间
        'exit_time',  # 出场时间
        'payment_display',  # 支付金额（带人民币符号）
        'paid',  # 支付状态
        'user'  # 关联用户
    )
    list_filter = ('vehicle_type', 'paid', 'reserved')
    search_fields = ('license_plate', 'user__username', 'order_number')

    def vehicle_type_display(self, obj):
        """显示中文车辆类型"""
        return dict(Vehicle.VEHICLE_TYPE_CHOICES).get(obj.vehicle_type, '未知类型')
    vehicle_type_display.short_description = '车辆类型'

    def payment_display(self, obj):
        """格式化支付金额显示"""
        if obj.payment_amount:
            return f"¥{obj.payment_amount:.2f}"
        return "未支付"
    payment_display.short_description = '支付金额'

    def display_fee(self, obj):
        """格式化显示费用"""
        return f"{obj.fee:.2f}元"
    display_fee.short_description = '费用'

    def get_parking_duration(self, obj):
        """计算并显示停车时长"""
        if obj.exit_time:
            return f"{obj.parking_duration_hours:.2f}小时"
        return f"在场中 ({obj.parking_duration_minutes}分钟)"
    get_parking_duration.short_description = '停车时长'

    def is_reserved(self, obj):
        """显示是否被预订"""
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
        """检查是否有权限访问此模块"""
        return request.user.is_active and request.user.is_superuser


@admin.register(User, site=custom_admin_site)
class UserAdmin(admin.ModelAdmin):
    """
    用户管理配置
    """
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
        """检查是否有权限访问此模块"""
        return request.user.is_active and request.user.is_superuser


@admin.register(ContactMessage, site=custom_admin_site)
class ContactMessageAdmin(admin.ModelAdmin):
    """
    招商合作信息管理配置
    """
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
        """检查是否有权限访问此模块"""
        return request.user.is_active and request.user.is_superuser


@admin.register(JobPosition, site=custom_admin_site)
class JobPositionAdmin(admin.ModelAdmin):
    """
    职位发布管理配置
    """
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
        """检查是否有权限访问此模块"""
        return request.user.is_active and request.user.is_superuser


@admin.register(Membership, site=custom_admin_site)
class MembershipAdmin(admin.ModelAdmin):
    """
    会员管理配置
    """
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
        """检查是否有权限访问此模块"""
        return request.user.is_active and request.user.is_superuser


@admin.register(Feedback, site=custom_admin_site)
class FeedbackAdmin(admin.ModelAdmin):
    """用户反馈管理配置"""
    list_display = ('user', 'get_feedback_type_display', 'content_short', 'created_at', 'is_resolved')
    list_filter = ('feedback_type', 'is_resolved')
    search_fields = ('content', 'user__username')
    list_editable = ('is_resolved',)
    readonly_fields = ('created_at',)

    fieldsets = (
        (None, {
            'fields': ('user', 'feedback_type', 'content', 'is_resolved')
        }),
        ('时间信息', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def content_short(self, obj):
        """显示内容的前50个字符"""
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