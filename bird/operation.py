from bird import models
import random
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import django.utils.timezone as timezone
from django.core.mail import send_mail
from django.conf import settings
import datetime;
from django.shortcuts import render, HttpResponse, redirect


def login_verification(data):
    username = data.get('username')
    try:
        if models.UserInfo.objects.filter(username=username).exists():
            error_msg = '用户名已存在'
            return 1, error_msg
    except Exception as e:
        error_msg = '输入不符合数据库要求'
        return 1, error_msg

    email = data.get('email')
    try:
        if models.UserInfo.objects.filter(email=email).exists():
            error_msg = '该邮箱已被注册'
            return 1, error_msg
    except Exception as e:
        error_msg = '输入不符合数据库要求'
        return 1, error_msg

    return 0, ''


def vcode():
    code = ''
    for i in range(0, 6):
        code = code + str(random.randint(0, 9))
    return code


def send_code(email, request):
    sender = 'bird_identify@126.com'
    password = 'HSQDBLRDXNTPNZOR'
    user = email
    try:
        '''
        code = vcode()
        msg = MIMEText('验证码为:'+code, 'plain', 'utf-8')
        msg['From'] = Header(sender, 'utf-8')
        msg['To'] = Header(user, 'utf-8')
        msg['Subject'] = Header('鸟类识别网站验证码', 'utf-8')
        server = smtplib.SMTP_SSL("smtp.126.com", 465)
        server.login(sender, password)
        server.sendmail(sender, [user, ], msg.as_string())
        server.quit()
        '''
        code = vcode()
        email_code = code
        msg = '验证码：' + email_code
        send_mail('邮箱验证', msg, settings.EMAIL_FROM,
                  [email])
        request.session['code'] = code
        request.session['time'] = datetime.datetime.now().timestamp()
        return 1

    except Exception as e:
        print(e)
        models.Diary.objects.create(info=e,
                                    record_time=timezone.now())
        return 0
