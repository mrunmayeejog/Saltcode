#
# Description: Utility functions to create,read and update json files
#

import sys
sys.path.append('../')
import copy
import json
import logging
import os
import shutil
from collections import OrderedDict
from threading import Lock
import config
from jobhandler.utils.exceptions import FileNotFound

log = logging.getLogger(__name__)

catalog_file_lock = Lock()
result_json_lock = Lock()
status_json_lock = Lock()
flow_json_lock = Lock()
update_flow_lock = Lock()
update_status_lock = Lock()
log_dir_creation_lock = Lock()
inventory_json_lock = Lock()


def create_json(template_id, json_data, json_file_name):
    json_dir = os.path.join(config.filestore, template_id)
    json_file = os.path.join(json_dir, json_file_name)
    log.debug("Creating " + json_file)
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)
    with open(json_file, 'w') as f:
        f.write(json.dumps(json_data, indent=4))

    log.debug("Created " + json_file)


def get_json(template_id, json_file_name):
    result_file = os.path.join(config.filestore,
                               template_id, json_file_name)

    print result_file
    log.debug('Fetching file: {}'.format(result_file))

    if not os.path.exists(result_file):
        log.error(json_file_name +
                  " not created for engagement: " + template_id)
        raise FileNotFound(result_file + " does not exist")

    with open(result_file) as json_file:
        json_data = json.load(json_file)

    return json_data


def put_json(template_id, json_data, json_file_name):
    result_dir = os.path.join(config.filestore, template_id)
    result_file = os.path.join(result_dir, json_file_name)
    log.debug("writing json to " + json_file_name)

    json_string = json.dumps(json_data, indent=4)
    with open(result_file, "w") as f:
        f.write(json_string)

    log.debug("updated " + json_file_name)


def delete_template(template_id):
    template_dir = os.path.join(config.filestore, template_id)
    shutil.rmtree(template_dir)
