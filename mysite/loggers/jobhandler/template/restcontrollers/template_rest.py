import sys
import json
from flask import request
from jobhandler.template.template_manager import Template


def load_template():
    response = {}
    template_id = Template.load_default_profile()
    response["template_id"] = template_id
    response["message"] = "Successfully initiated the template"
    return json.dumps(response)


def get_template(template_id):
    return json.dumps(Template(template_id).get_template(), sort_keys=True,
                      indent=10, separators=(',', ': '))


def update_template(template_id, template_operation):
    response = {}
    print type(request.data)
    print request.data
    data = json.loads(request.data)
    template = Template(template_id)
    if template_operation == 'add_tags':
        template.add_tag(data.get('tags'))
        response["template_id"] = template_id
        response["message"] = "Successfully tags added to the template"
        return json.dumps(response)

    if template_operation == 'add_nodes':

        if data.get('node_list'):
            template.add_nodes(data.get('node_list'))
            response["template_id"] = template_id
            response["message"] = "Successfully nodes added to the template"
        else:
            response["template_id"] = template_id
            response["message"] = "Unable to add nodes. Nodelist not empty"
        return json.dumps(response)
