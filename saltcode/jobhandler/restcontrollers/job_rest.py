import sys
import json
from flask import request
from jobhandler.job_manager import start_yarn_application, kill_yarn_application


def start_job(template_id):
    response = {}
    data = json.loads(request.data)
    resource_manager = data.get('resource_manager')
    job_details = data.get('job_details')
    tag = data.get('tag')
    print template_id, resource_manager, job_details, tag
    application_name = start_yarn_application(
        template_id, resource_manager, job_details=job_details, tag=tag)
    response["application_name"] = application_name
    response["message"] = "Successfully initiated the yarn application"
    return json.dumps(response)


def kill_job(template_id):
    response = {}
    data = json.loads(request.data)
    resource_manager = data.get('resource_manager')
    application_id = data.get('application_id')
    # print resource_manager,application_id
    try:
        if resource_manager and application_id:
            result = kill_yarn_application(resource_manager, application_id)
            response["application_id"] = application_id
            response["message"] = result
        else:
            response["message"] = "Invalid parameter pass to kill job"
    except Exception as e:
        response["message"] = str(e)
    return json.dumps(response)
