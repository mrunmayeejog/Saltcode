from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^upload/$', views.upload, name='upload'),
    url(r'^view/$', views.view_template, name = 'view'),
    url(r'^start/$', views.start_template, name = 'start'),
    url(r'^stop/$', views.stop_template, name = 'stop'),
    url(r'^teardown/$', views.teardown,name= 'teardown'),
    url(r'^monitor/start/$', views.start_hadoop_monitoring),
    url(r'^monitor/stop/$', views.stop_hadoop_monitoring)
]
