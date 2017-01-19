# Author : Anand Nevase
#
# Description: HTTP/REST interface for uploading template

import os
import json
import logging
from flask import request
from jobhandler import constants
from orchestrator import orch


def get_template(template_id):
    try:
        template = orch.get_template_stored(template_id=template_id)
        return json.dumps(template, sort_keys=True,
                          indent=10, separators=(',', ': '))
    except Exception as exception:
        #log.exception("Failed to upload template")
        raise Exception(
            "Template Not Found".format(str(exception)), constants.INTERNAL_SERVER_ERROR)


def post_upload():
    try:
        new_generated_eng_dir = None
        response = {}
        # check if the post request has the file part
        if 'file' not in request.files:
            raise Exception(
                "File not provided", constants.BAD_REQUEST)
        input_file = request.files['file']
        inputfile_name = input_file.filename
        if input_file and not allowed_file(inputfile_name):
            #log.exception("Uploaded file is not json file")
            raise Exception(
                "Uploaded file is not a json file. Please upload only a valid json file.", constants.BAD_REQUEST)

        template = json.loads(input_file.read())
        template_obj = orch.Template()
        template_id = template_obj.init_template(template=template)
        response["template_id"] = template_id
        response["template_name"] = template.get('name')
        response["message"] = "Successfully template uploaded "
        return json.dumps(response)

    except Exception as exception:
        #log.exception("Failed to upload template")
        raise Exception(
            "Failed to upload template {}".format(str(exception)), constants.INTERNAL_SERVER_ERROR)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ("json")
