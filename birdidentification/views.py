#!/usr/bin/env python
# coding:utf-8

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from django.shortcuts import render, redirect
import urllib
from urllib.request import urlopen
import base64
from PIL import Image
from io import BytesIO
from django.utils.safestring import mark_safe


def get_songs(birds):
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
    scientific_name = str(content[0])[3:-4]

    songs_url = 'https://www.xeno-canto.org/explore?query=' + quote(scientific_name)

    return scientific_name, songs_url


def main(request):
    if request.method == 'GET':
        return render(request, 'main.html')


def recognition_post(request):
    if request.method == 'GET':
        return render(request, 'main.html')
    if request.method == 'POST':
        file_obj = request.FILES.get('pic')
        pic = Image.open(file_obj).convert('RGB')
        host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=rENKxWSwY4OW4UmRGNKpKzTw&client_secret=Oojh1HqumwUNaPGnoGuSVFWqGcxyqvZw'
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
        for i in result:
            try:
                scientific_name, songs_url = get_songs(i['name'])
            except Exception as e:
                name_list.append(i['name'])
                score_list.append(i['score'])
                scientific_name_list.append('暂无结果')
                songs_url_list.append('暂无结果')
            else:
                name_list.append(i['name'])
                score_list.append(i['score'])
                scientific_name_list.append(scientific_name)
                songs_url_list.append(songs_url)
            url_list.append('https://baike.baidu.com/item/'+quote(i['name']))

        request.session['name'] = name_list
        request.session['score'] = score_list
        request.session['scientific_name'] = scientific_name_list
        request.session['songs_url'] = songs_url_list
        request.session['url'] = url_list

        if request.META.get('HTTP_X_FORWARDED_FOR'):
            ip = request.META.get("HTTP_X_FORWARDED_FOR")
        else:
            ip = request.META.get("REMOTE_ADDR")

        print("IP :", ip, '   upload picture size :', (w, h), '    result: ', name_list[0])
        return redirect('/result')


def result(request):
    if request.method == 'GET':
        content = {"name":request.session['name'], "score":request.session['score'],
                   "scientific_name": request.session['scientific_name'],
                   "songs_url": request.session['songs_url'], "url": request.session['url']}
        return render(request, 'result.html', content)
