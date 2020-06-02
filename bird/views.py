#!/usr/bin/env python
# coding:utf-8

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import urllib
from urllib.request import urlopen
import base64
from PIL import Image
from io import BytesIO
from django.shortcuts import render, HttpResponse, redirect
from bird import models, operation, image_process
from django.http import JsonResponse
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
import django.utils.timezone as timezone
import re
import ssl
from django.db.models import Q
import datetime
import cv2
import numpy

ssl._create_default_https_context = ssl._create_unverified_context


def register(request):
    if request.method == 'GET':
        if request.session.get('error_msg') is not None:
            error_msg = request.session.get('error_msg')
            del request.session['error_msg']
            return render(request, 'register.html', {"error_msg": error_msg})
        return render(request, 'register.html')
    elif request.method == 'POST':
        data = request.POST

        verification_code = operation.login_verification(data)
        if verification_code[0] == 1:
            request.session['error_msg'] = verification_code[1]
            return redirect('register')
        if data.get('password') != data.get('password_again'):
            request.session['error_msg'] = '两次输入密码不一致'
            return redirect('register')
        try:
            print(data)
            models.UserInfo.objects.create_user(username=data.get('username'),
                                                password=data.get('password'),
                                                email=data.get('email'),
                                                auth=0,
                                                record_time=timezone.now())
            # 接下来将注册成功的记录加入到记录表中
            models.Operation_record.objects.create(user_name=data.get('username'),
                                                   record_time=timezone.now(),
                                                   operation_code=5,  # 表示注册成功
                                                   )
        except Exception as e:
            models.Diary.objects.create(info=e,
                                        record_time=timezone.now())
            request.session['error_msg'] = '输入不符合数据库要求'
            return redirect('register')
        return redirect('login')


def login(request):
    if request.method == 'GET':
        if request.session.get('error_msg') is not None:
            error_msg = request.session.get('error_msg')
            del request.session['error_msg']
            return render(request, 'index.html', {"error_msg": error_msg})
        return render(request, 'index.html')
    elif request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            user_obj = auth.authenticate(username=username, password=password)
        except Exception as e:
            models.Diary.objects.create(info=e,
                                        record_time=timezone.now())
            request.session['error_msg'] = '输入不符合数据库要求'
            return redirect('login')
        if user_obj:
            auth.login(request, user_obj)
            #request.session['username'] = username  # 将用户名保存到session里    #这句是不需要的，会自动创建user对象
            models.Operation_record.objects.create(user_name=username,
                                                   operation_code=6,
                                                   record_time=timezone.now())

            return redirect('main')
        else:
            request.session['error_msg'] = "用户名或密码不正确"
            return redirect('login')


def logout(request):
    models.Operation_record.objects.create(user_name=request.user.username,
                                           operation_code=7,
                                           record_time=timezone.now())
    auth.logout(request)
    #username = request.POST.get('username')
    #request.session['username'] = username
    #del request.session['username']
    return redirect('login')


def code(request):
    if request.method == 'GET':
        email = request.GET['email']
        try:
            user = models.UserInfo.objects.get(email=email)
        except Exception as e:
            return HttpResponse('该邮箱未注册')
        request.session['email'] = email
        operation.send_code(email, request)
        return HttpResponse('发送成功')


@login_required
def change_passwd(request):
    if request.method == 'GET':
        if request.session.get('error_msg') is not None:
            error_msg = request.session.get('error_msg')
            del request.session['error_msg']
            return render(request, 'change_passwd.html', {"error_msg": error_msg})
        return render(request, 'change_passwd.html')

    if request.method == 'POST':
        data = request.POST
        if not request.user.check_password(data.get('old_password')):
            request.session['error_msg'] = '原始密码输入错误'
            return redirect('change_passwd')
        if data.get('password') != data.get('password_again'):
            request.session['error_msg'] = '两次输入密码不一致'
            return redirect('change_passwd')
        request.user.set_password(data.get('password'))
        request.user.save()
        models.Operation_record.objects.create(user_name=request.user.username,
                                               operation_code=3,
                                               record_time=timezone.now())
        messages.success(request, '修改成功')
        return redirect('main')


def forget_psw(request):
    if request.method == 'GET':
        if request.session.get('error_msg') is not None:
            error_msg = request.session.get('error_msg')
            del request.session['error_msg']
            return render(request, 'forget.html', {"error_msg": error_msg})
        return render(request, 'forget.html')
    elif request.method == 'POST':
        data = request.POST
        if data.get('password') != data.get('password_again'):
            request.session['error_msg'] = '两次输入密码不一致'
            return redirect('forget_psw')
        if request.session.get('time') - datetime.datetime.now().timestamp() > 300:
            request.session['error_msg'] = '操作时间太长，请重新发送验证码'
            return redirect('forget_psw')
        if data.get('code') == request.session.get('code'):
            user = models.UserInfo.objects.get(email=request.session['email'])
            user.set_password(data.get('password'))
            user.save()
            models.Operation_record.objects.create(user_name=user.username,
                                                   operation_code=3,
                                                   record_time=timezone.now())
            messages.success(request, '修改成功')
            return redirect('login')


def get_scientific_name(birds):
    base_url = 'https://baike.baidu.com/item/'
    pa = quote(birds)
    url = base_url + pa
    headers = {
        'User-Agent': '',
        'Cookie': ''
    }
    response = requests.get(url, headers=headers)
    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, 'lxml')

    content = soup.select('div.lemma-summary > div.para > i')
    str1 = str(content[0]).replace('<i>', '')
    str2 = str1.replace('</i>', '')
    scientific_name = str2
    return scientific_name


@login_required
def main(request):
    if request.method == 'GET':
        get_id = request.GET.get('id')
        print("得到")
        print(get_id)
        if get_id == None:
            content = {"name": request.user.username, }
            return render(request, 'main.html', content)
        else:
            if get_id[0]=="1":
                pic = Image.open("media/" + get_id[2:]).convert('RGB')
                host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&' \
                       'client_id=rENKxWSwY4OW4UmRGNKpKzTw&client_secret=Oojh1HqumwUNaPGnoGuSVFWqGcxyqvZw'
                apirequest = urllib.request.Request(host)
                apirequest.add_header('Content-Type', 'application/json; charset=UTF-8')
                response = urlopen(apirequest)
                content = response.read()
                content_str = str(content, encoding="utf-8")
                # eval将字符串转换成字典
                content_dir = eval(content_str)
                access_token = content_dir['access_token']

                request_url = "https://aip.baidubce.com/rest/2.0/image-classify/v1/animal"

                w, h = pic.size
                if w > 300:
                    pic.thumbnail((300, h / w * 300))

                output_buffer = BytesIO()
                pic.save(output_buffer, format='JPEG')
                byte_data = output_buffer.getvalue()
                img = base64.b64encode(byte_data)
                print(pic)
                params = {"image": img}
                params = urllib.parse.urlencode(params).encode(encoding='UTF8')

                request_url = request_url + "?access_token=" + access_token
                resrequest = urllib.request.Request(url=request_url, data=params)
                resrequest.add_header('Content-Type', 'application/x-www-form-urlencoded')
                response = urlopen(resrequest)  # too many time
                content = response.read()
                content_str = str(content, encoding="utf-8")
                content_dir = eval(content_str)
                result = content_dir['result']
                name_list = []
                score_list = []
                scientific_name_list = []
                songs_url_list = []
                url_list = []
                pos_list = []
                for i in result:
                    try:
                        scientific_name = get_scientific_name(i['name'])
                        print(scientific_name)
                        songs_url = 'https://www.xeno-canto.org/explore?query=' + quote(scientific_name)
                    except Exception as e:
                        name_list.append(i['name'])
                        score_list.append(i['score'])
                        scientific_name_list.append('暂无结果')
                        songs_url_list.append('暂无结果')
                        pos_list.append("暂无结果")
                    else:
                        name_list.append(i['name'])
                        score_list.append(i['score'])
                        scientific_name_list.append(scientific_name)
                        songs_url_list.append(songs_url)
                    if scientific_name_list[-1] != "暂无结果":
                        birds = models.All_Bird.objects.filter(sci_name__icontains=scientific_name_list[-1])
                        for bird in birds:
                            pos = "../media/" + bird.pos[9:]
                            pos_list.append(pos)
                    url_list.append('https://baike.baidu.com/item/' + quote(i['name']))
                request.session['name'] = name_list
                request.session['score'] = score_list
                request.session['scientific_name'] = scientific_name_list
                request.session['songs_url'] = songs_url_list
                request.session['baike_url'] = url_list
                request.session['pos_list'] = pos_list

                if request.META.get('HTTP_X_FORWARDED_FOR'):
                    ip = request.META.get("HTTP_X_FORWARDED_FOR")
                else:
                    ip = request.META.get("REMOTE_ADDR")

                print("IP :", ip, '   upload picture size :', (w, h), '    result: ', name_list[0])
                return redirect('/result')
            if get_id[0]=="2":
                username = request.user.username
                bird_name =get_id[2:]
                nameList = []
                sciNameList = []
                songsList = []
                baiduList = []
                manual = []
                content = {}
                birds = models.All_Bird.objects.filter(Q(name__icontains=bird_name) | Q(sci_name__icontains=bird_name))
                if birds == []:
                    content = {"name": ["暂无结果"], "scientific_name": ["暂无结果"], "songs_url ": ["暂无结果"],
                               "baike_url": ["暂无结果"], "info_url": ["暂无结果"], }
                    return render(request, 'find.html', content)
                else:
                    for bird in birds:
                        nameList.append(bird.name)
                        sciNameList.append(bird.sci_name)
                        pos = "../media/" + bird.pos[9:]
                        manual.append(pos)
                        songsList.append('https://www.xeno-canto.org/explore?query=' + quote(bird.sci_name))
                        baiduList.append('https://baike.baidu.com/item/' + quote(bird.name))
                        content = {
                            "name": nameList, "scientific_name": sciNameList, "songs_url": songsList,
                            "baike_url": baiduList, "info_url": manual,
                        }
                    return render(request, 'find.html', content)


def main_no_sign(request):
    if request.method == 'GET':
        get_id = request.GET.get('id')
        if get_id == None:
            return render(request, 'main_no_sign.html')
        else:
            if get_id[0]=="1":
                pic = Image.open("media/" + get_id[2:]).convert('RGB')
                host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&' \
                       'client_id=rENKxWSwY4OW4UmRGNKpKzTw&client_secret=Oojh1HqumwUNaPGnoGuSVFWqGcxyqvZw'
                apirequest = urllib.request.Request(host)
                apirequest.add_header('Content-Type', 'application/json; charset=UTF-8')
                response = urlopen(apirequest)
                content = response.read()
                content_str = str(content, encoding="utf-8")
                # eval将字符串转换成字典
                content_dir = eval(content_str)
                access_token = content_dir['access_token']

                request_url = "https://aip.baidubce.com/rest/2.0/image-classify/v1/animal"

                w, h = pic.size
                if w > 300:
                    pic.thumbnail((300, h / w * 300))

                output_buffer = BytesIO()
                pic.save(output_buffer, format='JPEG')
                byte_data = output_buffer.getvalue()
                img = base64.b64encode(byte_data)
                print(pic)
                params = {"image": img}
                params = urllib.parse.urlencode(params).encode(encoding='UTF8')

                request_url = request_url + "?access_token=" + access_token
                resrequest = urllib.request.Request(url=request_url, data=params)
                resrequest.add_header('Content-Type', 'application/x-www-form-urlencoded')
                response = urlopen(resrequest)  # too many time
                content = response.read()
                content_str = str(content, encoding="utf-8")
                content_dir = eval(content_str)
                result = content_dir['result']
                name_list = []
                score_list = []
                scientific_name_list = []
                songs_url_list = []
                url_list = []
                pos_list = []
                for i in result:
                    try:
                        scientific_name = get_scientific_name(i['name'])
                        print(scientific_name)
                        songs_url = 'https://www.xeno-canto.org/explore?query=' + quote(scientific_name)
                    except Exception as e:
                        name_list.append(i['name'])
                        score_list.append(i['score'])
                        scientific_name_list.append('暂无结果')
                        songs_url_list.append('暂无结果')
                        pos_list.append("暂无结果")
                    else:
                        name_list.append(i['name'])
                        score_list.append(i['score'])
                        scientific_name_list.append(scientific_name)
                        songs_url_list.append(songs_url)
                    if scientific_name_list[-1] != "暂无结果":
                        birds = models.All_Bird.objects.filter(sci_name__icontains=scientific_name_list[-1])
                        for bird in birds:
                            pos = "../media/" + bird.pos[9:]
                            pos_list.append(pos)
                    url_list.append('https://baike.baidu.com/item/' + quote(i['name']))
                request.session['name'] = name_list
                request.session['score'] = score_list
                request.session['scientific_name'] = scientific_name_list
                request.session['songs_url'] = songs_url_list
                request.session['baike_url'] = url_list
                request.session['pos_list'] = pos_list

                if request.META.get('HTTP_X_FORWARDED_FOR'):
                    ip = request.META.get("HTTP_X_FORWARDED_FOR")
                else:
                    ip = request.META.get("REMOTE_ADDR")

                print("IP :", ip, '   upload picture size :', (w, h), '    result: ', name_list[0])
                return redirect('/result')
            if get_id[0]=="2":
                bird_name =get_id[2:]
                nameList = []
                sciNameList = []
                songsList = []
                baiduList = []
                manual = []
                content = {}
                birds = models.All_Bird.objects.filter(Q(name__icontains=bird_name) | Q(sci_name__icontains=bird_name))
                if birds == []:
                    content = {"name": ["暂无结果"], "scientific_name": ["暂无结果"], "songs_url ": ["暂无结果"],
                               "baike_url": ["暂无结果"], "info_url": ["暂无结果"], }
                    return render(request, 'find_no_sign.html', content)
                else:
                    for bird in birds:
                        nameList.append(bird.name)
                        sciNameList.append(bird.sci_name)
                        pos = "../media/" + bird.pos[9:]
                        manual.append(pos)
                        songsList.append('https://www.xeno-canto.org/explore?query=' + quote(bird.sci_name))
                        baiduList.append('https://baike.baidu.com/item/' + quote(bird.name))
                        content = {
                            "name": nameList, "scientific_name": sciNameList, "songs_url": songsList,
                            "baike_url": baiduList, "info_url": manual,
                        }
                    return render(request, 'find_no_sign.html', content)


@login_required
def recognition_post(request):
    if request.method == 'GET':
        return render(request, 'main.html')
    if request.method == 'POST':
        username = request.user.username
        file_obj = request.FILES.get('pic')
        deal = request.POST.getlist('deal')
        print(file_obj)
        try:
            pic = Image.open(file_obj).convert('RGB')
        except Exception as e:
            messages.error(request,'未上传图片')
            return render(request, 'main.html', {"name": request.user.username, })
        pic = cv2.cvtColor(numpy.asarray(pic), cv2.COLOR_RGB2BGR)
        if "FENGE" in deal:
            pic = image_process.fenge(pic)
        if "RUIHUA" in deal:
            pic = image_process.ruihua(pic, 150)
        pic = Image.fromarray(cv2.cvtColor(pic, cv2.COLOR_BGR2RGB))
        host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&' \
               'client_id=rENKxWSwY4OW4UmRGNKpKzTw&client_secret=Oojh1HqumwUNaPGnoGuSVFWqGcxyqvZw'
        apirequest = urllib.request.Request(host)
        apirequest.add_header('Content-Type', 'application/json; charset=UTF-8')
        response = urlopen(apirequest)
        content = response.read()
        content_str = str(content, encoding="utf-8")
        # eval将字符串转换成字典
        content_dir = eval(content_str)
        access_token = content_dir['access_token']

        request_url = "https://aip.baidubce.com/rest/2.0/image-classify/v1/animal"

        w, h = pic.size
        if w > 300:
            pic.thumbnail((300, h / w * 300))

        output_buffer = BytesIO()
        pic.save(output_buffer, format='JPEG')
        byte_data = output_buffer.getvalue()
        img = base64.b64encode(byte_data)
        models.Operation_record.objects.create(user_name=username,
                                               operation_code=1,
                                               picture=file_obj,
                                               record_time=timezone.now())
        params = {"image": img}
        params = urllib.parse.urlencode(params).encode(encoding='UTF8')

        request_url = request_url + "?access_token=" + access_token
        resrequest = urllib.request.Request(url=request_url, data=params)
        resrequest.add_header('Content-Type', 'application/x-www-form-urlencoded')
        response = urlopen(resrequest)  # too many time
        content = response.read()
        content_str = str(content, encoding="utf-8")
        content_dir = eval(content_str)

        result = content_dir['result']

        name_list = []
        score_list = []
        scientific_name_list = []
        songs_url_list = []
        url_list = []
        pos_list = []
        for i in result:
            try:
                scientific_name = get_scientific_name(i['name'])
                print(scientific_name)
                songs_url = 'https://www.xeno-canto.org/explore?query=' + quote(scientific_name)
            except Exception as e:
                name_list.append(i['name'])
                score_list.append(i['score'])
                scientific_name_list.append('暂无结果')
                songs_url_list.append('暂无结果')
                pos_list.append("暂无结果")
            else:
                name_list.append(i['name'])
                score_list.append(i['score'])
                scientific_name_list.append(scientific_name)
                songs_url_list.append(songs_url)
            if scientific_name_list[-1] != "暂无结果":
                birds = models.All_Bird.objects.filter(sci_name__icontains=scientific_name_list[-1])
                '''
                for bird in birds:
                    pos = "../media/" + bird.pos[9:]
                    pos_list.append(pos)
                '''
                try:
                    pos_list.append("../media/" + birds[0].pos[9:])
                except Exception as e:
                    pos_list.append("暂无结果")
            url_list.append('https://baike.baidu.com/item/' + quote(i['name']))
        request.session['name'] = name_list
        request.session['score'] = score_list
        request.session['scientific_name'] = scientific_name_list
        request.session['songs_url'] = songs_url_list
        request.session['baike_url'] = url_list
        request.session['pos_list'] = pos_list
        if request.META.get('HTTP_X_FORWARDED_FOR'):
            ip = request.META.get("HTTP_X_FORWARDED_FOR")
        else:
            ip = request.META.get("REMOTE_ADDR")

        print("IP :", ip, '   upload picture size :', (w, h), '    result: ', name_list[0])
        return redirect('/result')


def recognition_no_sign(request):
    if request.method == 'GET':
        return render(request, 'main_no_sign.html')
    if request.method == 'POST':
        file_obj = request.FILES.get('pic')
        deal = request.POST.getlist('deal')
        print(file_obj)
        try:
            pic = Image.open(file_obj).convert('RGB')
        except Exception as e:
            messages.error(request, '未上传图片')
            return render(request, 'main.html')
        pic = cv2.cvtColor(numpy.asarray(pic), cv2.COLOR_RGB2BGR)
        if "FENGE" in deal:
            pic = image_process.fenge(pic)
        if "RUIHUA" in deal:
            pic = image_process.ruihua(pic, 150)
        pic = Image.fromarray(cv2.cvtColor(pic, cv2.COLOR_BGR2RGB))
        host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&' \
               'client_id=rENKxWSwY4OW4UmRGNKpKzTw&client_secret=Oojh1HqumwUNaPGnoGuSVFWqGcxyqvZw'
        apirequest = urllib.request.Request(host)
        apirequest.add_header('Content-Type', 'application/json; charset=UTF-8')
        response = urlopen(apirequest)
        content = response.read()
        content_str = str(content, encoding="utf-8")
        # eval将字符串转换成字典
        content_dir = eval(content_str)
        access_token = content_dir['access_token']

        request_url = "https://aip.baidubce.com/rest/2.0/image-classify/v1/animal"

        w, h = pic.size
        if w > 300:
            pic.thumbnail((300, h / w * 300))

        output_buffer = BytesIO()
        pic.save(output_buffer, format='JPEG')
        byte_data = output_buffer.getvalue()
        img = base64.b64encode(byte_data)
        params = {"image": img}
        params = urllib.parse.urlencode(params).encode(encoding='UTF8')

        request_url = request_url + "?access_token=" + access_token
        resrequest = urllib.request.Request(url=request_url, data=params)
        resrequest.add_header('Content-Type', 'application/x-www-form-urlencoded')
        response = urlopen(resrequest)  # too many time
        content = response.read()
        content_str = str(content, encoding="utf-8")
        content_dir = eval(content_str)

        result = content_dir['result']

        name_list = []
        score_list = []
        scientific_name_list = []
        songs_url_list = []
        url_list = []
        pos_list = []
        for i in result:
            try:
                scientific_name = get_scientific_name(i['name'])
                print(scientific_name)
                songs_url = 'https://www.xeno-canto.org/explore?query=' + quote(scientific_name)
            except Exception as e:
                name_list.append(i['name'])
                score_list.append(i['score'])
                scientific_name_list.append('暂无结果')
                songs_url_list.append('暂无结果')
                pos_list.append("暂无结果")
            else:
                name_list.append(i['name'])
                score_list.append(i['score'])
                scientific_name_list.append(scientific_name)
                songs_url_list.append(songs_url)
            if scientific_name_list[-1] != "暂无结果":
                birds = models.All_Bird.objects.filter(sci_name__icontains=scientific_name_list[-1])
                '''
                for bird in birds:
                    pos = "../media/" + bird.pos[9:]
                    pos_list.append(pos)
                '''
                try:
                    pos_list.append("../media/" + birds[0].pos[9:])
                except Exception as e:
                    pos_list.append("暂无结果")
            url_list.append('https://baike.baidu.com/item/' + quote(i['name']))
        request.session['name'] = name_list
        request.session['score'] = score_list
        request.session['scientific_name'] = scientific_name_list
        request.session['songs_url'] = songs_url_list
        request.session['baike_url'] = url_list
        request.session['pos_list'] = pos_list
        if request.META.get('HTTP_X_FORWARDED_FOR'):
            ip = request.META.get("HTTP_X_FORWARDED_FOR")
        else:
            ip = request.META.get("REMOTE_ADDR")

        print("IP :", ip, '   upload picture size :', (w, h), '    result: ', name_list[0])
        return redirect('/result_no_sign')


@login_required
def result(request):
    if request.method == 'GET':
        content = {"name": request.session['name'], "score": request.session['score'],
                   "scientific_name": request.session['scientific_name'],
                   "songs_url": request.session['songs_url'], "baike_url": request.session['baike_url'],
                   "info_url": request.session['pos_list'], }
        username = request.user.username
        return render(request, 'result.html', content)


def result_no_sign(request):
    if request.method == 'GET':
        content = {"name": request.session['name'], "score": request.session['score'],
                   "scientific_name": request.session['scientific_name'],
                   "songs_url": request.session['songs_url'], "baike_url": request.session['baike_url'],
                   "info_url": request.session['pos_list'], }
        return render(request, 'result_no_sign.html', content)


@login_required
def historical_actions(request):
    if request.method == 'GET':
        username = request.user.username
        user_op = models.Operation_record.objects.all()
        a_user = user_op.filter(user_name=username).order_by("-record_time")
        names = []
        record_times = []
        ops = []
        results = []
        for i in a_user:
            names.append(i.user_name)
            record_times.append(i.record_time)
            if i.operation_code == 1:
                ops.append("进行图像识别操作")
                results.append("1!"+str(i.picture))
            if i.operation_code == 2:
                ops.append("进行搜索功能")
                if i.website == "none":
                    results.append(("该次查询未查到结果"))
                else:
                    results.append("2!"+str(i.website))
            if i.operation_code == 3:
                ops.append("进行修改密码操作")
                results.append("成功")
            if i.operation_code == 4:
                ops.append("查看了历史操作记录")
                results.append("成功")
            if i.operation_code == 5:
                ops.append("您在这个时间进行了注册")
                results.append("成功")
            if i.operation_code == 6:
                ops.append("您在此时登陆了本系统")
                results.append("成功")
            if i.operation_code == 7:
                ops.append("您于此时退出了本系统")
                results.append("成功")
        content = {"username": username, "names": names, "ops": ops, "record_times": record_times, "results": results}
        models.Operation_record.objects.create(user_name=username,
                                               operation_code=4,
                                               record_time=timezone.now())
        return render(request, 'history.html', content)


@login_required
def find(request):
    if request.method == 'GET':
        return render(request, 'main.html')
    if request.method == 'POST':
        username = request.user.username
        bird_name = request.POST.get('bird_name')
        nameList = []
        sciNameList = []
        songsList = []
        baiduList = []
        manual = []
        content = {}
        birds = models.All_Bird.objects.filter(Q(name__icontains=bird_name) | Q(sci_name__icontains=bird_name))
        if len(birds)== 0:
            content = {"name": ["暂无结果"], "scientific_name": ["暂无结果"], "songs_url ": ["暂无结果"],
                       "baike_url": ["暂无结果"], "info_url": ["暂无结果"], }
            models.Operation_record.objects.create(user_name=username,
                                                   operation_code=2,
                                                   website="none",
                                                   record_time=timezone.now())
            return render(request, 'find.html', content)
        else:
            for bird in birds:
                nameList.append(bird.name)
                sciNameList.append(bird.sci_name)
                pos = "../media/" + bird.pos[9:]
                manual.append(pos)
                songsList.append('https://www.xeno-canto.org/explore?query=' + quote(bird.sci_name))
                baiduList.append('https://baike.baidu.com/item/' + quote(bird.name))
                content = {
                    "name": nameList, "scientific_name": sciNameList, "songs_url": songsList,
                    "baike_url": baiduList, "info_url": manual,
                }

            models.Operation_record.objects.create(user_name=username,
                                                   operation_code=2,
                                                   website=bird_name,
                                                   record_time=timezone.now())

            return render(request, 'find.html', content)


def find_no_sign(request):
    if request.method == 'GET':
        return render(request, 'main_no_sign.html')
    if request.method == 'POST':
        bird_name = request.POST.get('bird_name')
        nameList = []
        sciNameList = []
        songsList = []
        baiduList = []
        manual = []
        content = {}
        birds = models.All_Bird.objects.filter(Q(name__icontains=bird_name) | Q(sci_name__icontains=bird_name))
        if len(birds)== 0:
            content = {"name": ["暂无结果"], "scientific_name": ["暂无结果"], "songs_url ": ["暂无结果"],
                       "baike_url": ["暂无结果"], "info_url": ["暂无结果"], }
            return render(request, 'find_no_sign.html', content)
        else:
            for bird in birds:
                nameList.append(bird.name)
                sciNameList.append(bird.sci_name)
                pos = "../media/" + bird.pos[9:]
                manual.append(pos)
                songsList.append('https://www.xeno-canto.org/explore?query=' + quote(bird.sci_name))
                baiduList.append('https://baike.baidu.com/item/' + quote(bird.name))
                content = {
                    "name": nameList, "scientific_name": sciNameList, "songs_url": songsList,
                    "baike_url": baiduList, "info_url": manual,
                }

            return render(request, 'find_no_sign.html', content)


def about(request):
    if request.method == 'GET':
        return render(request, 'about.html')