from django.contrib import admin
from django.urls import path, include
from parking_app.admin import custom_admin_site  # 导入自定义AdminSite

urlpatterns = [
    path('admin/', custom_admin_site.urls),  # 只使用自定义AdminSite
    path('', include('parking_app.urls')),  # 包含应用的URL配置
]