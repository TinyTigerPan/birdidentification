from django.shortcuts import render, HttpResponse, redirect
import urllib
from urllib.request import urlopen
import base64


def main(request):
    if request.method == 'GET':
        return render(request, 'main.html')


def recognition_post(request):
    if request.method == 'GET':
        return render(request, 'main.html')
    if request.method == 'POST':
        file_obj = request.FILES.get('pic')
        host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=rENKxWSwY4OW4UmRGNKpKzTw&client_secret=Oojh1HqumwUNaPGnoGuSVFWqGcxyqvZw'
        apirequest = urllib.request.Request(host)
        apirequest.add_header('Content-Type', 'application/json; charset=UTF-8')
        response = urlopen(apirequest)
        content = response.read()
        content_str = str(content, encoding="utf-8")
        # eval将字符串转换成字典
        content_dir = eval(content_str)
        access_token = content_dir['access_token']
        print(access_token)

        request_url = "https://aip.baidubce.com/rest/2.0/image-classify/v1/animal"


        # 二进制方式打开图片文件
        f = file_obj
        img = base64.b64encode(f.read())


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

        result_score = result[0]['score']
        result_name = result[0]['name']

        request.session['name'] = result_name
        request.session['score'] = result_score

        return redirect('/result')


def result(request):
    if request.method == 'GET':
        content = {"score": request.session['score'], "name": request.session['name']}
        return render(request, 'result.html', content)