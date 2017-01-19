import sys
import json
from flask import request
from orchestrator import orch
from jobhandler import constants


def start_hadoop_monitoring(template_id):
    response, data = {}, {}

    '''
    if request.data:
        data = json.loads(request.data)
    '''
    try:
        template_obj = orch.Template()
        template_id = template_obj.init_template(template_id=template_id)
    except Exception as exception:
        # log.exception("Failed to upload template")
        raise Exception(
            "Template Not Found : {}".format(str(exception)), constants.INTERNAL_SERVER_ERROR)

    # Call to orchestrator for monitoring.
    try:
        # deploy Poller template
        template_obj.deploy_template_poller()
        # Start Poller template
        template_obj.start_template_poller()
        response["message"] = "Successfully initiated the monitoring"
        response["template_id"] = template_id
        return json.dumps(response)
    except Exception as exception:
        raise Exception(
            "Failed to start the monitoring: {}".format(str(exception)), constants.INTERNAL_SERVER_ERROR)


def stop_hadoop_monitoring(template_id):
    response = {}
    try:
        template_obj = orch.Template()
        template_id = template_obj.init_template(template_id=template_id)

    except Exception as exception:
        # log.exception("Failed to upload template")
        raise Exception(
            "Template Not Found".format(str(exception)), constants.INTERNAL_SERVER_ERROR)

    # Call to orchestrator for stop monitoring.
    try:
        # STOP  Poller template
        template_obj.stop_template_poller()
        response["message"] = "Successfully stopped the monitoring"
        response["template_id"] = template_id
        return json.dumps(response)
    except Exception as exception:
        raise Exception(
            "Failed to start the monitoring".format(str(exception)), constants.INTERNAL_SERVER_ERROR)
