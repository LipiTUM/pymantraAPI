"""pymantra_api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from .views import *

ROOT = settings.ROOT_DOMAIN
if ROOT:
    urlpatterns = [
        path(f'{ROOT}/admin/', admin.site.urls),
        path(f'{ROOT}/verify-connection', verify_connection),
        path(f'{ROOT}/database/', include('database.urls')),
    ]
else:
    urlpatterns = [
        path('admin/', admin.site.urls),
        path('verify-connection', verify_connection),
        path('database/', include('database.urls')),
    ]
