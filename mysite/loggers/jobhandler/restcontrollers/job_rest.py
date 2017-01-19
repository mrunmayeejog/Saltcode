import sys
import json
import time
import thread
from flask import request
from jobhandler.job_manager import start_yarn_application, kill_yarn_application
from orchestrator import orch
from jobhandler import constants


def start_job(template_id):

    try:
        template_obj = orch.get_template_obj(template_id=template_id)
    except Exception as exception:
        # log.exception("Failed to upload template")
        raise Exception(
            "Template Not Found : {}".format(str(exception)), constants.INTERNAL_SERVER_ERROR)

    if template_obj:
        # Start YARN JOB
        response = {}
        data = json.loads(request.data)
        resource_manager = data.get('resource_manager')
        template_obj.get_template()
        job_details = data.get('job_details')
        tag = data.get('tag')
        application_name = start_yarn_application(
            template_id, resource_manager, job_details=job_details, tag=tag)

        # Update Job poller
        job_meta = template_obj.get_poller_plugin_meta(
            plugin_name=constants.JOB_POLLER)

        app_names = job_meta.get('application_names')
        app_names.append(application_name)
        template_obj.update_poller_plugin_meta(
            plugin_name=constants.JOB_POLLER, meta=job_meta)
        thread.start_new_thread(
            monitor_poller_application, (template_obj, application_name))
        response["application_name"] = application_name
        response["message"] = "Successfully initiated the yarn application"
        return json.dumps(response)


def monitor_poller_application(template_obj, application_name):
    while True:
        job_plugin_status = template_obj.get_poller_plugin_status(
            plugin_name=constants.JOB_POLLER)
        print "================================================"
        print "APP {} STATUS:{} ".format(application_name,job_plugin_status)
        print "================================================"

        for app in job_plugin_status.get('applications_status'):
            if app['application_name'] == application_name:
                if app['status'] in ['FINISHED']:
                    job_meta = template_obj.get_poller_plugin_meta(
                        plugin_name=constants.JOB_POLLER)
                    if application_name in job_meta.get('application_names'):
                        job_meta.get('application_names').remove(
                            application_name)
                        template_obj.update_poller_plugin_meta(
                            plugin_name=constants.JOB_POLLER, meta=job_meta)
                        print "APP {} REMOVE".format(application_name)
                        return
        time.sleep(10)
    return None


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
