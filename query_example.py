import os
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parking_system.settings')
django.setup()

# 导入你的模型
from parking_app.models import Vehicle, User, Membership

def query_vehicles():
    """
    查询 Vehicle 表的所有数据
    """
    print("查询 Vehicle 表：")
    vehicles = Vehicle.objects.all()
    for vehicle in vehicles:
        print(
            f"车牌号: {vehicle.license_plate}, "
            f"车辆类型: {vehicle.vehicle_type}, "
            f"用户: {vehicle.user.username}, "
            f"入场时间: {vehicle.entry_time}, "
            f"出场时间: {vehicle.exit_time}, "
            f"是否支付: {vehicle.paid}, "
            f"车位号: {vehicle.spot_number}, "
            f"是否被预订: {vehicle.reserved}, "
            f"预订时间: {vehicle.reservation_time}"
        )

def query_users():
    """
    查询 User 表的所有数据
    """
    print("\n查询 User 表：")
    users = User.objects.all()
    for user in users:
        print(
            f"用户名: {user.username}, "
            f"邮箱: {user.email}, "
            f"手机号: {user.phone_number}, "
            f"创建时间: {user.created_at}, "
            f"是否是超级用户: {user.is_superuser}"
        )

def query_memberships():
    """
    查询 Membership 表的所有数据
    """
    print("\n查询 Membership 表：")
    memberships = Membership.objects.all()
    for membership in memberships:
        print(
            f"用户: {membership.user.username}, "
            f"会员类型: {membership.membership_type}, "
            f"开始时间: {membership.start_date}, "
            f"结束时间: {membership.end_date}, "
            f"是否有效: {membership.is_active()}"
        )

if __name__ == "__main__":
    # 执行查询
    query_vehicles()
    query_users()
    query_memberships()