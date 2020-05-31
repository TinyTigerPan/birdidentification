"""birdidentification URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import url
from bird import views
from django.conf.urls.static import static
from birdidentification import settings

from django.views.generic.base import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^$', views.login),
    url(r'^login', views.login, name='login'),
    url(r'^register', views.register, name='register'),
    url(r'^forget', views.forget_psw, name='forget_psw'),
    url(r'^code/', views.code, name='code'),
    url(r'^main', views.main, name='main'),
    url(r'^recognition/', views.recognition_post, name='recognition'),
    url(r'^change_passwd/', views.change_passwd, name='change_passwd'),
    url(r'^result$', views.result, name='result'),
    url(r'^history', views.historical_actions, name='history'),
    url(r'^find', views.find, name='find'),

]+static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
