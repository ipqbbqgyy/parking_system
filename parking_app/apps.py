# parking_app/apps.py
from django.apps import AppConfig

class ParkingAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'parking_app'
    verbose_name = '凉心智慧停车系统'
