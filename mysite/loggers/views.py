# Create your views here.

from django.http import HttpResponse
import os, json
from loggers.template import TemplateApp
from django.views.decorators.csrf import csrf_exempt
from django.core.context_processors import csrf
tm = TemplateApp()



def extract_template_id(request):
    data = json.loads(request.body)
    print data.get('template_id')
    return data.get('template_id')	
	



def upload(request):
    response = tm.upload_template()
    return HttpResponse(json.dumps(response))


@csrf_exempt
def view_template(request):
    if request.method == 'POST':
	template_id = extract_template_id(request)
        template_obj = tm.get_template(template_id = template_id)
        temp = json.dumps(template_obj.get_template(), sort_keys=True,indent=10, separators=(',', ': '))	
        return HttpResponse(temp)

@csrf_exempt
def start_template(request):
    if request.method == 'POST':
	response = {}
	template_id = extract_template_id(request)
        template_obj = tm.get_template(template_id = template_id)
        response["template_id"] = template_id
        response["message"] = "Successfully template started "
        template_obj.start_subtemplate(subtemp_name="ALL NODES", op_level='loggers')
	return HttpResponse(json.dumps(response))	

@csrf_exempt
def stop_template(request):
    if request.method == 'POST':
        response = {}
	template_id = extract_template_id(request)
        template_obj = tm.get_template(template_id = template_id)
        response["template_id"] = template_id
        response["message"] = "Successfully template stopped "
        template_obj.stop_subtemplate(subtemp_name="ALL NODES", op_level='loggers')
        return HttpResponse(json.dumps(response))


@csrf_exempt
def start_hadoop_monitoring(request):
    if request.method == 'POST':
	template_id = extract_template_id(request)
        response = tm.start_hadoop_monitoring(template_id = template_id)
        return HttpResponse(response)

@csrf_exempt
def stop_hadoop_monitoring(request):
    if request.method == 'POST':
	template_id = extract_template_id(request)
        response = tm.stop_hadoop_monitoring(template_id = template_id)
        return HttpResponse(response)


@csrf_exempt
def teardown(request,template_id=''):
    if request.method == 'POST':
        template_obj = tm.get_template(template_id = template_id)
        template_obj.teardown_subtemp()   
