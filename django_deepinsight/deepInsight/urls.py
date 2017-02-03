from django.conf.urls import url, include
# from django.contrib import admin
from watchdog.monitor_apis import *

urlpatterns = [
    url(r'^template/', include('template.urls')),
    url(r'^monitor/(?P<tid>.+)/(?P<oper>.+)$', ClusterMonitor.monitor, name='start'),
]
