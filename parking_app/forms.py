from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        error_messages={
            'required': '邮箱是必填项',
            'invalid': '请输入有效的邮箱地址',
            'unique': '邮箱已存在',
        }
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        error_messages={
            'max_length': '手机号不能超过 15 个字符',
        }
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 自定义密码错误信息
        self.fields['password1'].error_messages = {
            'required': '密码是必填项',
            'password_too_short': '密码太短',
            'password_too_common': '密码太常见',
            'password_entirely_numeric': '密码不能全是数字',
        }
        self.fields['password2'].error_messages = {
            'required': '确认密码是必填项',
            'password_mismatch': '输入的两个密码不一致',
        }
        self.fields['username'].error_messages = {
            'required': '用户名是必填项',
            'unique': '用户名已存在',
        }

        def save(self, commit=True):
            user = super().save(commit=False)
            user.set_password(self.cleaned_data["password1"])  # 确保密码被加密
            if commit:
                user.save()
            return user