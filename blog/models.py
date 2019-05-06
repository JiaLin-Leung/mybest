from django.db import models

# Create your models here.


class User(models.Model):

    username = models.CharField("用户名",max_length=11)
    password = models.CharField("密码",max_length=11)
    regin_data = models.DateTimeField("注册时间",auto_now=True)
