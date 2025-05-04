from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import logging
from decimal import Decimal, ROUND_HALF_UP
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid

# 获取当前模块的日志记录器
logger = logging.getLogger(__name__)

def generate_order_number():
    """生成订单号的函数"""
    return f"PARK-{uuid.uuid4().hex[:8].upper()}"

class Feedback(models.Model):
    """用户反馈模型"""
    FEEDBACK_TYPES = [
        ('suggestion', '建议'),
        ('problem', '问题'),
        ('complaint', '投诉'),
        ('other', '其他'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES, verbose_name='反馈类型')
    content = models.TextField(verbose_name='反馈内容')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    is_resolved = models.BooleanField(default=False, verbose_name='是否已处理')

    class Meta:
        verbose_name = '用户反馈'
        verbose_name_plural = '用户反馈'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_feedback_type_display()} - {self.user.username if self.user else '匿名用户'}"

class AdminActionLogger:
    """管理员操作日志记录器，用于记录管理员的各种操作"""

    @staticmethod
    def log(request, action, obj=None, message=""):
        """
        静态方法，记录管理员操作日志

        参数:
            request: HttpRequest对象，包含用户信息
            action: 操作类型(create/update/delete等)
            obj: (可选)操作的对象实例
            message: (可选)自定义日志消息
        """
        try:
            # 初始化内容类型和对象ID
            content_type = None
            object_id = None

            # 如果提供了对象，获取其内容类型和ID
            if obj:
                content_type = ContentType.objects.get_for_model(obj)
                object_id = obj.pk

            # 如果没有提供消息，根据操作和对象生成默认消息
            if not message and obj:
                model_name = content_type.model if content_type else '未知模型'
                message = f"{AdminLogEntry.ACTION_DISPLAY.get(action, action)} {model_name}: {str(obj)}"

            # 创建管理员日志条目
            AdminLogEntry.objects.create(
                user=request.user,
                action=action,
                content_type=content_type,
                object_id=object_id,
                message=message
            )
        except Exception as e:
            # 记录错误日志
            logger.error(f"记录管理员操作时出错: {str(e)}", exc_info=True)

class Promotion(models.Model):
    """促销活动模型，用于管理停车场的促销折扣活动"""

    # 折扣类型选项
    DISCOUNT_TYPE_CHOICES = [
        ('percent', '百分比'),  # 百分比折扣
        ('fixed', '固定金额'),  # 固定金额减免
    ]

    # 模型字段定义
    name = models.CharField(max_length=50, verbose_name='促销名称')  # 促销活动名称
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, default='percent',
                                     verbose_name='折扣类型')  # 折扣类型
    discount_value = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='折扣值')  # 折扣数值
    start_time = models.DateTimeField(verbose_name='开始时间')  # 活动开始时间
    end_time = models.DateTimeField(verbose_name='结束时间')  # 活动结束时间
    is_active = models.BooleanField(default=True, verbose_name='是否生效')  # 是否激活
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')  # 创建时间

    def is_valid(self):
        """检查促销活动当前是否有效"""
        now = timezone.now()
        return self.is_active and self.start_time <= now <= self.end_time

    def get_discount_display(self):
        """获取折扣信息的显示字符串"""
        if self.discount_type == 'percent':
            return f"{100 - float(self.discount_value)}% 折扣"  # 百分比折扣显示
        return f"立减 {self.discount_value}元"  # 固定金额减免显示

    class Meta:
        # 元数据配置
        verbose_name = '促销活动'  # 单数名称
        verbose_name_plural = '促销活动'  # 复数名称
        ordering = ['-start_time']  # 默认按开始时间降序排列

    def __str__(self):
        """对象字符串表示"""
        return f"{self.name} ({self.start_time.date()} 至 {self.end_time.date()})"

class Vehicle(models.Model):
    """车辆模型，用于管理停车场中的车辆信息"""

    # 车辆类型选项
    VEHICLE_TYPE_CHOICES = [
        ('car', '小型汽车'),  # 普通小型汽车
        ('truck', '货车'),  # 货车
        ('ev', '新能源车'),  # 新能源电动车
    ]

    # 模型字段定义
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='vehicles')  # 关联用户
    license_plate = models.CharField(max_length=20, verbose_name='车牌号')  # 车牌号码
    vehicle_type = models.CharField(
        max_length=20,
        choices=VEHICLE_TYPE_CHOICES,
        default='car',
        verbose_name='车辆类型'
    )  # 车辆类型
    entry_time = models.DateTimeField(default=timezone.now, null=True, blank=True, verbose_name='入场时间')  # 入场时间
    exit_time = models.DateTimeField(null=True, blank=True, verbose_name='出场时间')  # 出场时间
    paid = models.BooleanField(default=False, verbose_name='是否支付')  # 是否已支付
    spot_number = models.CharField(max_length=10, blank=True, null=True, verbose_name='车位号')  # 车位编号
    reserved = models.BooleanField(default=False, verbose_name='是否被预订')  # 是否被预订
    reservation_time = models.DateTimeField(null=True, blank=True, verbose_name='预订时间')  # 预订时间
    reservation_use_time = models.DateTimeField(null=True, blank=True, verbose_name='预定使用时间')  # 预定使用时间
    reservation_expiry_time = models.DateTimeField(null=True, blank=True, verbose_name='预定过期时间')  # 预定过期时间
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='费用')  # 停车费用
    order_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name='订单号',
        default=generate_order_number  # 使用函数而不是lambda
    )
    payment_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='支付金额'
    )

    def save(self, *args, **kwargs):
        """保存模型时自动生成订单号和计算费用"""
        if not self.order_number:
            self.order_number = generate_order_number()
        if self.exit_time:
            self.fee = self.calculate_fee()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        """生成订单号"""
        if not self.order_number:
            self.order_number = generate_order_number()
        return self.order_number

    # 常量定义
    FREE_DURATION_MINUTES = 5  # 免费停车时长(分钟)
    HOURLY_RATE = Decimal('5')  # 每小时停车费率(元)

    def get_vehicle_type_display(self):
        """获取车辆类型的显示名称"""
        return dict(self.VEHICLE_TYPE_CHOICES).get(self.vehicle_type, '未知类型')

    @property
    def vehicle_type_chinese(self):
        """返回中文车辆类型(属性方式访问)"""
        return dict(self.VEHICLE_TYPE_CHOICES).get(self.vehicle_type, '未知类型')

    @property
    def parking_duration_minutes(self):
        """计算停车时长(分钟)"""
        if not self.entry_time:
            return 0

        # 如果有出场时间使用出场时间，否则使用当前时间
        exit_time = self.exit_time if self.exit_time else timezone.now()

        # 处理时区问题
        if timezone.is_aware(self.entry_time) and timezone.is_aware(exit_time):
            duration = exit_time - self.entry_time
        else:
            # 如果时间不是时区感知的，转换为UTC时区
            entry_utc = timezone.make_aware(self.entry_time) if not timezone.is_aware(
                self.entry_time) else self.entry_time
            exit_utc = timezone.make_aware(exit_time) if not timezone.is_aware(exit_time) else exit_time
            duration = exit_utc - entry_utc

        # 返回分钟数，保留2位小数
        return round(duration.total_seconds() / 60, 2)

    @property
    def parking_duration_hours(self):
        """计算停车时长(小时)"""
        minutes = self.parking_duration_minutes
        return round(minutes / 60, 2)

    @property
    def formatted_duration(self):
        """格式化显示停车时长(小时和分钟)"""
        minutes = self.parking_duration_minutes
        hours = int(minutes // 60)
        remaining_minutes = int(minutes % 60)
        return f"{hours}小时{remaining_minutes}分钟"

    def calculate_original_fee(self, duration_hours=None):
        """
        计算原始停车费用(不考虑任何折扣)

        参数:
            duration_hours: (可选)指定的小时数，如果不提供则根据停车时长计算

        返回:
            Decimal类型的费用金额
        """
        # 如果是会员且会员有效，费用为0
        if hasattr(self.user, 'membership') and self.user.membership.is_active():
            return Decimal('0.00')

        if not self.entry_time:
            return Decimal('0.00')

        # 如果没有提供时长参数，则计算实际停车时长
        if duration_hours is None:
            duration_minutes = self.parking_duration_minutes
            # 如果停车时间在免费时长内，费用为0
            if duration_minutes <= self.FREE_DURATION_MINUTES:
                return Decimal('0.00')
            duration_hours = Decimal(str(duration_minutes)) / Decimal('60')

        # 计算费用 = 时长 × 小时费率
        fee = Decimal(str(duration_hours)) * self.HOURLY_RATE
        # 四舍五入到2位小数
        return fee.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)

    def calculate_fee(self):
        """计算实际停车费用(考虑会员和促销活动)"""
        # 如果是会员且会员有效，费用为0
        if hasattr(self.user, 'membership') and self.user.membership.is_active():
            self.payment_amount = Decimal('0.00')
            return self.payment_amount

        if not self.entry_time:
            return Decimal('0.00')

        duration_minutes = self.parking_duration_minutes

        # 如果停车时间在免费时长内，费用为0
        if duration_minutes <= self.FREE_DURATION_MINUTES:
            return Decimal('0.00')

        # 计算分钟费率
        minute_rate = self.HOURLY_RATE / Decimal('60')
        fee = Decimal(str(duration_minutes)) * minute_rate

        now = timezone.now()
        exit_time = self.exit_time if self.exit_time else now

        # 查询有效促销活动(当前时间在活动时间范围内)
        valid_promotions = Promotion.objects.filter(
            is_active=True,
            start_time__lte=exit_time,
            end_time__gte=self.entry_time
        )

        # 如果没有促销活动，直接返回原价
        if not valid_promotions.exists():
            return fee.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)

        # 应用促销折扣
        promotion = valid_promotions.first()
        try:
            if promotion.discount_type == 'percent':
                # 百分比折扣
                discount = fee * (promotion.discount_value / Decimal('100'))
                fee -= discount
            elif promotion.discount_type == 'fixed':
                # 固定金额减免
                fee -= promotion.discount_value

            # 确保费用不低于0
            fee = max(fee, Decimal('0.00'))
        except Exception as e:
            logger.error(f"应用促销时出错: {str(e)}")

        # 四舍五入到2位小数
        self.payment_amount = fee.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
        return self.payment_amount

    @staticmethod
    def clean_expired_reservations():
        """清理过期的车辆预订"""
        Vehicle.objects.filter(
            reserved=True,
            reservation_expiry_time__lt=timezone.now()
        ).delete()

    class Meta:
        # 元数据配置
        verbose_name = '车辆'  # 单数名称
        verbose_name_plural = '车辆'  # 复数名称

    def __str__(self):
        """对象字符串表示"""
        return self.license_plate

def calculate_original_fee(parking_duration_hours, hourly_rate=Decimal('5')):
    """
    独立函数：计算原始停车费用

    参数:
        parking_duration_hours: 停车时长(小时)
        hourly_rate: 每小时费率(默认5元)

    返回:
        Decimal类型的费用金额
    """
    fee = Decimal(str(parking_duration_hours)) * hourly_rate
    return fee.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)

class User(AbstractUser):
    """自定义用户模型，扩展了Django的AbstractUser"""

    # 模型字段定义
    email = models.EmailField(unique=True, verbose_name='邮箱')  # 邮箱(唯一)
    phone_number = models.CharField(max_length=15, blank=True, null=True, verbose_name='手机号')  # 手机号
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')  # 创建时间
    is_superuser = models.BooleanField(default=False, verbose_name='是否是超级用户')  # 超级用户标志

    def has_active_membership(self):
        """检查用户是否有有效的会员资格"""
        return hasattr(self, 'membership') and self.membership.is_active()

    class Meta:
        # 元数据配置
        verbose_name = '用户'  # 单数名称
        verbose_name_plural = '用户'  # 复数名称

    def save(self, *args, **kwargs):
        """保存用户时自动加密密码"""
        if self.password and not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

class Membership(models.Model):
    """会员模型，用于管理用户的会员资格"""

    # 会员类型选项
    MEMBERSHIP_CHOICES = [
        ('month', '一个月'),  # 月度会员
        ('quarter', '一个季度'),  # 季度会员
        ('year', '一年'),  # 年度会员
    ]

    # 模型字段定义
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='membership')  # 关联用户(一对一)
    membership_type = models.CharField(max_length=10, choices=MEMBERSHIP_CHOICES, verbose_name='会员类型')  # 会员类型
    start_date = models.DateTimeField(default=timezone.now, verbose_name='开始时间')  # 会员开始时间
    end_date = models.DateTimeField(verbose_name='结束时间')  # 会员结束时间

    def is_active(self):
        """检查会员资格当前是否有效"""
        return timezone.now() <= self.end_date

    def get_membership_type_display(self):
        """获取会员类型的显示名称"""
        return dict(self.MEMBERSHIP_CHOICES).get(self.membership_type, '')

    class Meta:
        # 元数据配置
        verbose_name = "会员"  # 单数名称
        verbose_name_plural = "会员"  # 复数名称
        ordering = ['-start_date']  # 默认按开始时间降序排列

    def __str__(self):
        """对象字符串表示"""
        return f"{self.user.username} - {self.get_membership_type_display()}"

class ContactMessage(models.Model):
    """联系消息模型，用于存储用户提交的联系信息"""

    # 模型字段定义
    name = models.CharField(max_length=100, verbose_name="姓名")  # 联系人姓名
    email = models.EmailField(verbose_name="邮箱")  # 联系人邮箱
    message = models.TextField(verbose_name="消息")  # 联系消息内容
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")  # 创建时间

    class Meta:
        # 元数据配置
        verbose_name = "招商合作"  # 单数名称
        verbose_name_plural = "招商合作"  # 复数名称

class JobPosition(models.Model):
    """职位模型，用于管理招聘职位信息"""

    # 模型字段定义
    title = models.CharField(max_length=100, verbose_name="职位名称")  # 职位名称
    description = models.TextField(verbose_name="职位描述")  # 职位描述
    requirements = models.TextField(verbose_name="职位要求")  # 职位要求
    location = models.CharField(max_length=100, verbose_name="工作地点")  # 工作地点
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")  # 创建时间

    class Meta:
        # 元数据配置
        verbose_name = "职位发布"  # 单数名称
        verbose_name_plural = "职位发布"  # 复数名称

class AdminLogEntry(models.Model):
    """管理员日志条目模型，用于记录管理员操作"""

    # 操作类型选项
    ACTION_CHOICES = [
        ('create', '创建'),  # 创建操作
        ('update', '修改'),  # 修改操作
        ('delete', '删除'),  # 删除操作
        ('view', '查看'),  # 查看操作
        ('login', '登录'),  # 登录操作
        ('logout', '登出'),  # 登出操作
        ('other', '其他操作'),  # 其他操作
    ]

    # 操作类型显示映射
    ACTION_DISPLAY = {
        'create': '创建',
        'update': '修改',
        'delete': '删除',
        'view': '查看',
        'login': '登录',
        'logout': '登出',
        'other': '其他操作',
    }

    # 模型字段定义
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)  # 操作用户
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)  # 操作类型
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True)  # 内容类型(关联模型)
    object_id = models.PositiveIntegerField(null=True, blank=True)  # 对象ID
    message = models.TextField()  # 日志消息
    timestamp = models.DateTimeField(auto_now_add=True)  # 时间戳

    class Meta:
        # 元数据配置
        verbose_name = "管理员日志"  # 单数名称
        verbose_name_plural = "管理员日志"  # 复数名称
        ordering = ['-timestamp']  # 默认按时间戳降序排列

    def __str__(self):
        """对象字符串表示"""
        return f"{self.user} - {self.get_action_display()} - {self.content_type}"

    def get_action_display(self):
        """获取操作类型的显示名称"""
        return self.ACTION_DISPLAY.get(self.action, self.action)