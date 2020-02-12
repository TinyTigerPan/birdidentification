from django.shortcuts import render, HttpResponse, redirect
import urllib
from urllib.request import urlopen
import base64
from PIL import Image
from io import BytesIO


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

        result_list = []
        for i in result:
            result_list.append([i['name'], i['score']])

        request.session['result'] = result_list

        if request.META.get('HTTP_X_FORWARDED_FOR'):
            ip = request.META.get("HTTP_X_FORWARDED_FOR")
        else:
            ip = request.META.get("REMOTE_ADDR")

        print("IP :", ip, '   upload picture size :', (w, h), '    result: ', result_list)

        return redirect('/result')


def result(request):
    if request.method == 'GET':
        content = {"result": request.session['result']}
        return render(request, 'result.html', content)