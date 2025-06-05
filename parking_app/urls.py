from django.urls import include, path
from django.urls import path
from django.views.generic import TemplateView
from parking_app import views
from django.conf import settings
from django.conf.urls.static import static
#社区版就是有这个报错，可以忽略
from .views import ChangePasswordView, admin_dashboard, exit_vehicle, vehicle_history, buy_membership
# vehicle_entry  # 使用相对导入修改密码视图
from .views import EditProfileView  # 导入编辑资料的视图
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.views.generic import TemplateView
from .views import vehicle_data
from .admin import custom_admin_site

urlpatterns = [
    # 首页和静态页面
    path('', views.home, name='home'),  # 网站首页
    path('company_introduction/', views.company_introduction, name='company_introduction'),  # 公司介绍页面
    path('parking/', views.parking, name='parking'),  # 停车场概览页面
    path('parking_lot/', views.parking_lot, name='parking_lot'),  # 停车管理系统主页面
    path('parking_lot/data/', views.parking_lot_data, name='parking_lot_data'),  # 停车数据API接口
    path('help/', views.help, name='help'),  # 帮助中心页面
    path('business_cooperation/', views.business_cooperation, name='business_cooperation'),  # 招商合作页面
    path('we/', views.we, name='we'),  # 个人中心页面
    path('contact/', views.contact, name='contact'),  # 联系我们页面
    path('submit-contact-form/', views.submit_contact_form, name='submit_contact_form'),  # 提交联系表单的接口
    # 加入我们相关页面
    path('contact-us/', views.contact_us, name='contact_us'),  # 联系我们页面(备用)
    path('join_us/', views.join_us, name='join_us'),  # 招聘信息列表页
    # path('join_us/', views.join_us),  # 新增兼容路径
    path('job/<int:job_id>/', views.job_detail, name='job_detail'),  # 职位详情页

    # 用户认证相关路由
    path('login/', views.login_home, name='login'),  # 登录页面
    path('login_v/', views.login_v, name='login'),  # 登录处理接口
    path('register/', views.register, name='register'),  # 注册页面
    path('register_v/', views.register_v, name='register_v'),  # 注册处理接口
    path('logout/', views.logout_view, name='logout'),  # 退出登录接口
    path('change_password/', ChangePasswordView.as_view(), name='change_password'),  # 修改密码页面
    path('edit_profile/', EditProfileView.as_view(), name='edit_profile'),  # 编辑资料页面
    path('buy_membership/', buy_membership, name='buy_membership'),  # 会员购买页面

    # 管理员相关路由
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),  # 管理员仪表盘
    path('feedback_history/', views.feedback_history, name='feedback_history'),#反馈记录
    path('submit_feedback/', views.submit_feedback, name='submit_feedback'),#反馈信息
    # 停车场管理相关路由
    path('use_reservation/<int:vehicle_id>/', views.use_reservation, name='use_reservation'),  # 使用预订车位接口
    path('reserve_spot/', views.reserve_spot, name='reserve_spot'),  # 预订车位接口
    path('cancel_reservation/<int:vehicle_id>/', views.cancel_reservation, name='cancel_reservation'),  # 取消预订接口
    path('vehicle_history/', vehicle_history, name='vehicle_history'),  # 停车记录页面
    path('validate_license_plate/', views.validate_license_plate, name='validate_license_plate'),  # 验证车牌号接口
    path('entry/', views.entry, name='entry'),  # 车辆入场接口
    path('exit_vehicle/<int:vehicle_id>/', views.exit_vehicle, name='exit_vehicle'),  # 车辆出场页面
    path('payment/<int:vehicle_id>/', views.payment, name='payment'),  # 支付处理接口
]

