# 导入必要的模块和类
import logging
import math
import re
from datetime import datetime
from datetime import timedelta
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import UpdateView
from .forms import RegisterForm
from .models import Membership, ContactMessage, JobPosition, Promotion, \
    calculate_original_fee  # 直接从 models.py 中导入 Membership
from .models import User
from .models import Vehicle
from django.http import JsonResponse
from .models import Feedback
import json
from django.core import serializers
from django.http import JsonResponse


def feedback_history(request):
    if request.method == 'GET':
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'message': '请先登录'})

        try:
            feedbacks = Feedback.objects.filter(user=request.user).order_by('-created_at')
            feedback_list = []

            for feedback in feedbacks:
                feedback_list.append({
                    'feedback_type': feedback.feedback_type,
                    'feedback_type_display': feedback.get_feedback_type_display(),
                    'content': feedback.content,
                    'created_at': feedback.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'is_resolved': feedback.is_resolved
                })

            return JsonResponse({
                'success': True,
                'feedbacks': feedback_list
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': '无效的请求方法'})

#反馈信息
def submit_feedback(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            feedback = Feedback.objects.create(
                user=request.user if request.user.is_authenticated else None,
                feedback_type=data.get('feedback_type'),
                content=data.get('content')
            )
            return JsonResponse({'success': True, 'message': '反馈已提交'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': '无效的请求方法'})



# 收入数据API视图（仅限超级用户访问）
@user_passes_test(lambda u: u.is_superuser)
@csrf_exempt
def income_data(request):
    # 获取查询时间段参数，默认为今天
    period = request.GET.get('period', 'today')
    # 获取当前时区（Asia/Shanghai）
    tz = timezone.get_current_timezone()  

    # 获取当前本地时间并计算查询范围
    now_local = timezone.localtime(timezone.now())
    if period == 'today':
        # 今天开始时间（00:00:00）
        start_date = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        # 本周开始时间（周一00:00:00）
        start_date = now_local - timedelta(days=now_local.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'month':
        # 本月第一天开始时间
        start_date = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == 'quarter':
        # 当前季度的第一天
        current_quarter = (now_local.month - 1) // 3 + 1
        start_date = now_local.replace(month=(current_quarter - 1) * 3 + 1, day=1,
                                     hour=0, minute=0, second=0, microsecond=0)
    elif period == 'year':
        # 本年第一天
        start_date = now_local.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:  # all
        # 所有时间段
        start_date = None

    # 构建查询条件：已支付且已出库的车辆
    query = Vehicle.objects.filter(paid=True)
    if start_date:
        # 将本地时间转换为UTC时间
        start_date_utc = timezone.make_naive(start_date, tz).astimezone(timezone.utc)
        query = query.filter(exit_time__gte=start_date_utc)

    # 处理记录数据（转换为本地时间）
    records = []
    for vehicle in query.order_by('-exit_time')[:20]:
        # 将UTC时间转换为本地时间
        local_time = timezone.localtime(vehicle.exit_time)
        records.append({
            'date': local_time.strftime('%Y-%m-%d %H:%M'),  # 格式化本地时间
            'license_plate': vehicle.license_plate,
            'duration': vehicle.parking_duration,
            'amount': float(vehicle.calculate_fee()),
            'is_member': hasattr(vehicle.user, 'membership') and vehicle.user.membership.is_active()
        })

    # 生成趋势数据
    trend_data = {'labels': [], 'amounts': []}
    if period == 'today':
        # 按小时统计
        hours = {h: 0.0 for h in range(24)}
        for v in query:
            local_hour = timezone.localtime(v.exit_time).hour
            hours[local_hour] += float(v.calculate_fee())
        trend_data['labels'] = [f"{h:02d}:00" for h in range(24)]
        trend_data['amounts'] = list(hours.values())
    elif period in ['week', 'month']:
        # 按天统计
        days = {}
        for v in query:
            local_date = timezone.localtime(v.exit_time).strftime('%m-%d')
            days[local_date] = days.get(local_date, 0) + float(v.calculate_fee())
        trend_data['labels'] = sorted(days.keys())
        trend_data['amounts'] = [days[k] for k in trend_data['labels']]
    elif period in ['quarter', 'year']:
        # 按月统计
        months = {}
        for v in query:
            local_month = timezone.localtime(v.exit_time).strftime('%Y-%m')
            months[local_month] = months.get(local_month, 0) + float(v.calculate_fee())
        trend_data['labels'] = sorted(months.keys())
        trend_data['amounts'] = [months[k] for k in trend_data['labels']]

    # 返回JSON响应
    return JsonResponse({
        'success': True,
        'stats': {
            'total_income': sum(float(v.calculate_fee()) for v in query),
            'avg_daily_income': sum(float(v.calculate_fee()) for v in query) / (7 if period == 'week' else 1),
            'max_daily_income': max(trend_data['amounts']) if trend_data['amounts'] else 0,
            'parking_count': query.count()
        },
        'trend': trend_data,
        'records': records
    })

# 自定义JSON编码器，处理datetime对象
class DateTimeEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            # 将datetime对象转换为ISO格式字符串
            return obj.isoformat()
        return super().default(obj)

# 车辆数据API视图（仅限超级用户访问）
@user_passes_test(lambda u: u.is_superuser)
@csrf_exempt
def vehicle_data(request):
    try:
        # 检查用户是否已认证
        if not request.user.is_authenticated:
            return JsonResponse({
                "success": False,
                "message": "用户未登录",
                "login_url": "/admin/"  # 指向admin登录页面
            }, status=401)

        # 获取分页参数
        limit = int(request.GET.get('limit', 100))  # 每页记录数，默认100
        offset = int(request.GET.get('offset', 0))  # 偏移量，默认0

        # 构建查询集
        if request.user.is_superuser:
            # 超级用户可以查看所有车辆
            queryset = Vehicle.objects.all().order_by('-entry_time')
        else:
            # 普通用户只能查看自己的车辆
            queryset = Vehicle.objects.filter(user=request.user).order_by('-entry_time')

        # 获取总数和分页数据
        total_count = queryset.count()
        vehicles = list(queryset[offset:offset + limit].values(
            'id',
            'license_plate',
            'spot_number',
            'entry_time',
            'exit_time',
            'vehicle_type',
            'user__username'
        ))

        # 返回JSON响应
        return JsonResponse({
            "success": True,
            "total": total_count,
            "count": len(vehicles),
            "vehicles": vehicles
        }, encoder=DateTimeEncoder)  # 使用自定义编码器

    except Exception as e:
        # 异常处理
        return JsonResponse({
            "success": False,
            "message": "服务器错误",
            "error": str(e)
        }, status=500)

# 车辆类型映射
VEHICLE_TYPE_MAPPING = {
    'car': '小型汽车',
    'truck': '货车',
    'ev': '新能源车',
}

# 日志记录器
logger = logging.getLogger(__name__)

# 示例日志记录视图
def my_view(request):
    logger.debug("This is a debug message.")
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.")

# 普通车牌号的正则表达式
STANDARD_PLATE_REGEX = r'^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领][A-HJ-NP-Z][A-HJ-NP-Z0-9]{4,5}[A-HJ-NP-Z0-9挂学警港澳]$'

# 新能源车牌号的正则表达式
NEW_ENERGY_PLATE_REGEX = r'^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领][A-HJ-NP-Z](?:[A-HJ-NP-Z0-9]{4}|[D-F][A-HJ-NP-Z0-9]{5})$'

# 车牌号验证函数
def is_license_plate_valid(license_plate):
    """
    验证车牌号是否规范
    :param license_plate: 车牌号
    :return: True 如果车牌号规范，否则 False
    """
    # 检查普通车牌号
    if re.match(STANDARD_PLATE_REGEX, license_plate):
        return True
    # 检查新能源车牌号
    if re.match(NEW_ENERGY_PLATE_REGEX, license_plate):
        return True
    return False

# 车牌号验证API
@csrf_exempt
def validate_license_plate(request):
    if request.method == 'POST':
        # 获取车牌号并去除前后空格
        license_plate = request.POST.get('license_plate', '').strip()

        # 验证车牌号是否规范
        if is_license_plate_valid(license_plate):
            return JsonResponse({"success": True, "message": "车牌号格式正确"})
        else:
            return JsonResponse({"success": False, "message": "车牌号格式不规范"})

    return JsonResponse({"success": False, "message": "无效的请求方法"})

# 首页视图
def home(request):
    return render(request, "home.html")

# 公司介绍视图
def company_introduction(request):
    return render(request, "company_introduction.html")

# 停车场概览视图
def parking(request):
    return render(request, "parking.html")

# 招商合作视图
def business_cooperation(request):
    return render(request, "business_cooperation.html")

# 联系我们视图
def contact(request):
    return render(request, 'contact.html')

# 提交联系表单视图
def submit_contact_form(request):
    if request.method == 'POST':
        # 获取表单数据
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        # 将数据保存到数据库
        ContactMessage.objects.create(name=name, email=email, message=message)

        # 添加成功消息
        messages.success(request, '您的消息已成功发送！我们将尽快与您联系。')

        # 重定向到联系页面
        return redirect('contact')
    else:
        # 如果不是POST请求，重定向到联系页面
        return redirect('contact')

# 招聘信息列表视图
def join_us(request):
    # 获取所有职位
    jobs = JobPosition.objects.all()
    return render(request, 'join_us.html', {'jobs': jobs})

# 职位详情视图
def job_detail(request, job_id):
    # 获取指定ID的职位，如果不存在返回404
    job = get_object_or_404(JobPosition, id=job_id)
    return render(request, 'job_detail.html', {'job': job})

# 联系我们视图(备用)
def contact_us(request):
    return render(request, 'contact-us.html')  

# 停车记录视图
def vehicle_history(request):
    if request.user.is_superuser:
        # 超级用户查看所有停车记录
        vehicles = Vehicle.objects.all()
    else:
        # 普通用户查看自己的停车记录
        vehicles = Vehicle.objects.filter(user=request.user)
    return render(request, "vehicle_history.html", {"vehicles": vehicles})

# 停车管理系统主视图
@login_required(login_url='/login/')
def parking_lot(request):
    # 清理过期的预订记录
    Vehicle.clean_expired_reservations()

    # 获取当前有效的促销活动
    active_promotion = Promotion.objects.filter(
        is_active=True,
        start_time__lte=timezone.now(),
        end_time__gte=timezone.now()
    ).first()

    # 查询实际占用的车位（非预订）
    occupied_spots = Vehicle.objects.filter(
        exit_time__isnull=True,
        reserved=False
    ).values_list('spot_number', flat=True)

    # 查询未过期的预订车位
    reserved_spots = Vehicle.objects.filter(
        reserved=True,
        exit_time__isnull=True,
        reservation_expiry_time__gt=timezone.now()
    ).values_list('spot_number', flat=True)

    # 定义所有车位的初始状态
    spots = []
    # A区车位(1-15)
    for num in range(1, 16):
        spots.append({"id": f"A{num}", "status": "available"})
    # B区车位(1-24)
    for num in range(1, 25):
        spots.append({"id": f"B{num}", "status": "available"})
    # C区车位(1-23)
    for num in range(1, 24):
        spots.append({"id": f"C{num}", "status": "available"})
    # D区车位(1-12)
    for num in range(1, 13):
        spots.append({"id": f"D{num}", "status": "available"})
    # E区车位(1-11)
    for num in range(1, 12):
        spots.append({"id": f"E{num}", "status": "available"})

    # 更新车位状态
    for spot in spots:
        if spot["id"] in occupied_spots:
            spot["status"] = "occupied"  # 已占用
        elif spot["id"] in reserved_spots:
            spot["status"] = "reserved"  # 已预订
        else:
            spot["status"] = "available"  # 可用

    return render(request, "parking_lot.html", {
        "spots": spots,
        "active_promotion": active_promotion  # 传递促销活动信息
    })

# 停车数据API
@login_required
def parking_lot_data(request):
    # 清理过期的预订记录
    Vehicle.clean_expired_reservations()

    # 获取当前有效的促销活动
    active_promotion = Promotion.objects.filter(
        is_active=True,
        start_time__lte=timezone.now(),
        end_time__gte=timezone.now()
    ).first()

    # 查询实际占用的车位（非预订）
    occupied_spots = Vehicle.objects.filter(
        exit_time__isnull=True,
        reserved=False
    ).values_list('spot_number', flat=True)

    # 查询未过期的预订车位
    reserved_spots = Vehicle.objects.filter(
        reserved=True,
        exit_time__isnull=True,
        reservation_expiry_time__gt=timezone.now()
    ).values_list('spot_number', flat=True)

    # 定义所有车位的初始状态
    spots = []
    # 同上，初始化所有车位
    for num in range(1, 16):
        spots.append({"id": f"A{num}", "status": "available"})
    for num in range(1, 25):
        spots.append({"id": f"B{num}", "status": "available"})
    for num in range(1, 24):
        spots.append({"id": f"C{num}", "status": "available"})
    for num in range(1, 13):
        spots.append({"id": f"D{num}", "status": "available"})
    for num in range(1, 12):
        spots.append({"id": f"E{num}", "status": "available"})

    # 更新车位状态
    for spot in spots:
        if spot["id"] in occupied_spots:
            spot["status"] = "occupied"
        elif spot["id"] in reserved_spots:
            spot["status"] = "reserved"
        else:
            spot["status"] = "available"

    # 构建返回数据
    response_data = {
        "spots": spots,
        "active_promotion": None
    }

    # 如果有促销活动，添加促销信息
    if active_promotion:
        response_data["active_promotion"] = {
            "name": active_promotion.name,
            "discount": active_promotion.get_discount_display(),
            "start_time": active_promotion.start_time.isoformat(),
            "end_time": active_promotion.end_time.isoformat()
        }

    return JsonResponse(response_data)

# 帮助中心视图
def help(request):
    return render(request, "help.html")

# 个人中心视图
@login_required(login_url='/login/')
def we(request):
    user = request.user
    current_time = timezone.now()

    # 清理过期的预订记录
    Vehicle.clean_expired_reservations()

    if user.is_superuser:
        # 超级用户查看所有车辆
        all_vehicles = Vehicle.objects.filter(reserved=False, exit_time__isnull=True)
        reserved_vehicles = Vehicle.objects.filter(reserved=True, exit_time__isnull=True)
    else:
        # 普通用户查看自己的车辆
        all_vehicles = Vehicle.objects.filter(user=user, reserved=False, exit_time__isnull=True)
        reserved_vehicles = Vehicle.objects.filter(user=user, reserved=True, exit_time__isnull=True)

    # 获取所有未过期的预订记录
    all_reservations = Vehicle.objects.filter(
        user=user,
        reserved=True,
        reservation_expiry_time__gt=current_time  # 只显示未过期的预订
    )

    return render(request, "we.html", {
        'user': user,
        'all_vehicles': all_vehicles,
        'reserved_vehicles': reserved_vehicles,
        'all_reservations': all_reservations,
        'current_time': current_time,
    })

# 登录页面视图
def login_home(request):
    # 检查用户是否已登录
    if request.user.is_authenticated:
        return redirect('we')  # 如果已登录，跳转到个人中心
    return render(request, "login.html")

# 注册页面视图
def register(request):
    # 检查用户是否已登录
    if request.user.is_authenticated:
        return redirect('we')  # 如果已登录，跳转到个人中心
    return render(request, "register.html")

# 登录处理视图
def login_v(request):
    # 调试日志
    logger.debug(f"访问登录页面，方法：{request.method}，认证状态：{request.user.is_authenticated}")

    # 检查用户是否已登录
    if request.user.is_authenticated:
        return redirect('we')

    if request.method == 'POST':
        # 获取POST数据
        post_data = request.POST.dict()
        logger.debug(f"收到POST数据：{post_data}")

        # 获取表单数据
        slider_value = post_data.get('slider_value', '0')  # 滑块验证值
        username = post_data.get('username', '').strip()  # 用户名
        password = post_data.get('password', '')  # 密码
        client_ip = request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR')  # 客户端IP

        # 人机验证(滑块必须滑到100)
        if slider_value != '100':
            logger.warning(f"[安全验证] IP：{client_ip} 滑块验证失败（值：{slider_value}）")
            messages.error(request, '请完成人机验证！')
            return redirect('login')

        # 字段验证
        if not username or not password:
            logger.warning(f"[输入验证] IP：{client_ip} 用户名或密码为空")
            messages.error(request, '用户名和密码不能为空！')
            return redirect('login')

        # 用户认证
        user = authenticate(request, username=username, password=password)
        if user:
            # 认证成功，登录用户
            login(request, user)
            logger.info(f"[登录成功] 用户：{username} IP：{client_ip}")
            return redirect('we')
        else:
            # 认证失败
            logger.warning(f"[登录失败] 用户：{username} IP：{client_ip}")
            messages.error(request, '用户名或密码错误！')

    return render(request, 'login.html')

# 注册处理视图
def register_v(request):
    # 检查用户是否已登录
    if request.user.is_authenticated:
        return redirect('we')

    if request.method == 'POST':
        # 使用表单验证
        form = RegisterForm(request.POST)

        # 验证人机验证滑块
        slider_value = request.POST.get('slider_value', '')
        if slider_value != '100':
            messages.error(request, '请完成人机验证')
            return render(request, 'register.html', {'form': form})

        # 表单验证
        if form.is_valid():
            # 验证通过，保存用户
            user = form.save()
            # 登录用户
            login(request, user)
            messages.success(request, '注册成功！')
            return redirect('we')
        else:
            # 表单验证失败，显示错误信息
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            return render(request, 'register.html', {'form': form})
    else:
        # GET请求，显示空表单
        form = RegisterForm()

    # 清除可能存在的消息
    storage = messages.get_messages(request)
    for message in storage:
        pass

    return render(request, 'register.html', {'form': form})

# 会员购买视图
@login_required
def buy_membership(request):
    if request.method == 'POST':
        # 获取会员类型
        membership_type = request.POST.get('membership_type')
        user = request.user

        # 根据会员类型计算结束日期
        if membership_type == 'month':
            end_date = timezone.now() + timedelta(days=30)  # 一个月
        elif membership_type == 'quarter':
            end_date = timezone.now() + timedelta(days=90)  # 一个季度
        elif membership_type == 'year':
            end_date = timezone.now() + timedelta(days=365)  # 一年
        else:
            messages.error(request, '无效的会员类型')
            return redirect('buy_membership')

        # 创建或更新会员
        Membership.objects.update_or_create(
            user=user,
            defaults={
                'membership_type': membership_type,
                'start_date': timezone.now(),  # 开始时间为当前时间
                'end_date': end_date,  # 结束时间
            }
        )
        messages.success(request, '会员购买成功！')
        return redirect('we')

    return render(request, 'buy_membership.html')

# 编辑资料视图类
class EditProfileView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ['username', 'email', 'phone_number']  # 允许编辑的字段
    template_name = 'edit_profile.html'  # 模板路径
    success_url = reverse_lazy('we')  # 成功后跳转到个人中心

    def get_object(self, queryset=None):
        # 获取当前登录用户
        return self.request.user

# 修改密码视图类
class ChangePasswordView(PasswordChangeView):
    template_name = 'change_password.html'  # 模板路径
    success_url = reverse_lazy('we')  # 成功后跳转到个人中心

# 退出登录视图
def logout_view(request):
    auth_logout(request)  # 调用Django内置的logout函数
    messages.success(request, '您已成功退出登录！')
    return redirect('home')

# 管理员仪表盘视图
@staff_member_required  # 仅限管理员访问
def admin_dashboard(request):
    # 获取最近的10条车辆记录
    vehicles = Vehicle.objects.all().order_by('-entry_time')[:10]
    return render(request, 'admin/index.html', {'vehicles': vehicles})

# 车辆入场API
@csrf_exempt
def entry(request):
    if request.method == 'POST':
        # 清理所有过期的预订记录
        current_time = timezone.now()
        expired_reservations = Vehicle.objects.filter(
            reserved=True,
            reservation_expiry_time__lt=current_time
        )

        # 将过期的预订记录的车位状态更新为"可用"
        for reservation in expired_reservations:
            reservation.reserved = False
            reservation.reservation_expiry_time = None
            reservation.reservation_use_time = None
            reservation.save()

        # 获取表单数据
        license_plate = request.POST.get('license_plate', '').strip()
        spot_number = request.POST.get('spot_number', '').strip()
        vehicle_type = request.POST.get('vehicle_type', '').strip()
        user = request.user

        # 验证车牌号是否规范
        if not is_license_plate_valid(license_plate):
            return JsonResponse({"success": False, "message": "车牌号格式不规范"})

        # 检查车牌号是否已经在未出库的车辆中
        if Vehicle.objects.filter(license_plate=license_plate, exit_time__isnull=True).exists():
            return JsonResponse({"success": False, "message": "该车辆已在停车场内"})

        # 检查车位是否已经被占用或预订
        if Vehicle.objects.filter(spot_number=spot_number, exit_time__isnull=True).exists():
            return JsonResponse({"success": False, "message": "该车位已被占用或预订"})

        try:
            # 创建车辆记录并关联车位号 - 使用本地时间
            vehicle = Vehicle(
                license_plate=license_plate,
                vehicle_type=vehicle_type,
                user=user,
                spot_number=spot_number,
                entry_time=timezone.localtime(timezone.now())  # 使用本地时间
            )
            vehicle.save()
            return JsonResponse({"success": True, "message": "车辆入场成功"})
        except Exception as e:
            return JsonResponse({"success": False, "message": f"发生错误：{str(e)}"})

    return JsonResponse({"success": False, "message": "无效的请求方法"})

# 预订车位API
@csrf_exempt
def reserve_spot(request):
    if request.method == 'POST':
        # 获取用户输入的时间
        reservation_use_time = request.POST.get('reservation_use_time', '').strip()
        license_plate = request.POST.get('license_plate', '').strip()
        vehicle_type = request.POST.get('vehicle_type', '').strip()
        spot_number = request.POST.get('spot_number', '').strip()

        # 解析时间并转换为本地时间
        use_time = timezone.datetime.strptime(reservation_use_time, '%Y-%m-%dT%H:%M')
        use_time = timezone.make_aware(use_time)  # 转换为带时区的datetime对象
        use_time = timezone.localtime(use_time)  # 转换为本地时间

        # 从数据库获取预订过期时间(分钟)
        expiry_minutes = Vehicle.get_reservation_expiry_minutes()

        # 计算过期时间(使用时间 + 过期分钟数)
        expiry_time = use_time + timezone.timedelta(minutes=expiry_minutes)

        # 创建预订记录
        try:
            vehicle = Vehicle.objects.create(
                user=request.user,
                license_plate=license_plate,
                vehicle_type=vehicle_type,
                spot_number=spot_number,
                reserved=True,
                reservation_time=timezone.now(),  # 当前时间
                reservation_use_time=use_time,  # 预订使用时间
                reservation_expiry_time=expiry_time  # 过期时间
            )
            return JsonResponse({
                "success": True,
                "message": "预订成功",
                "redirect_url": "/we/"
            })
        except Exception as e:
            return JsonResponse({"success": False, "message": f"发生错误：{str(e)}"})
    return JsonResponse({"success": False, "message": "无效的请求方法"})


# 使用预订车位API
@login_required
@csrf_exempt
def use_reservation(request, vehicle_id):
    if request.method == 'POST':
        try:
            # 获取车辆记录
            vehicle = Vehicle.objects.get(id=vehicle_id)
            if vehicle.reserved:
                current_time = timezone.now()
                # 检查是否到了使用时间
                if current_time < vehicle.reservation_use_time:
                    return JsonResponse({
                        "success": False,
                        "message": "还未到使用时间"
                    })

                # 更新车辆状态为已使用
                vehicle.reserved = False
                vehicle.entry_time = current_time
                vehicle.save()
                return JsonResponse({
                    "success": True,
                    "message": "车位已使用",
                    "redirect_url": "/we/"  # 跳转URL
                })
        except Vehicle.DoesNotExist:
            return JsonResponse({"success": False, "message": "车辆不存在"})
    return JsonResponse({"success": False, "message": "无效请求"})

# 取消预订API
@login_required(login_url='/login/')
@csrf_exempt
def cancel_reservation(request, vehicle_id):
    if request.method == 'POST':
        try:
            # 获取车辆记录
            vehicle = Vehicle.objects.get(id=vehicle_id)
            if vehicle.reserved:
                # 删除预订记录
                vehicle.delete()
                return JsonResponse({
                    "success": True,
                    "message": "预订已取消，记录已删除",
                    "redirect_url": "/we/"  # 跳转URL
                })
            return JsonResponse({"success": False, "message": "该记录不是预订记录"})
        except Vehicle.DoesNotExist:
            return JsonResponse({"success": False, "message": "车辆不存在"})
    return JsonResponse({"success": False, "message": "无效的请求方法"})

# 车辆出场视图
csrf_protect


@login_required
def exit_vehicle(request, vehicle_id):
    # 获取车辆记录
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    now = timezone.now()

    # 计算停车时长(小时)
    duration = (now - vehicle.entry_time).total_seconds() / 3600
    exact_duration = duration
    parking_duration = math.ceil(duration)  # 向上取整

    # 计算费用
    original_fee = calculate_original_fee(parking_duration)
    fee = vehicle.calculate_fee()

    # 检查是否有有效的促销活动
    has_promotion = Promotion.objects.filter(
        is_active=True,
        start_time__lte=now,
        end_time__gte=now
    ).exists()

    # 构建上下文
    context = {
        'vehicle': vehicle,
        'now': now,
        'parking_duration': parking_duration,
        'exact_duration': round(exact_duration, 2),
        'fee': fee,
        'original_fee': original_fee,
        'has_promotion': has_promotion,  # 添加促销活动标志
    }

    return render(request, 'payment_partial.html', context)


# 支付处理API
@csrf_protect
def payment(request, vehicle_id):
    if request.method == 'POST':
        try:
            # 获取车辆记录
            vehicle = Vehicle.objects.get(id=vehicle_id)
            # 更新出场时间和支付状态
            vehicle.exit_time = timezone.now()
            vehicle.paid = True
            vehicle.save()
            return JsonResponse({"success": True, "message": "支付成功"})
        except Vehicle.DoesNotExist:
            return JsonResponse({"success": False, "message": "车辆信息不存在"})
    return JsonResponse({"success": False, "message": "无效的请求方法"})