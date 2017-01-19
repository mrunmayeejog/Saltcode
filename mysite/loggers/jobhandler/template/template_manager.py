import json
import os
from jobhandler.utils import filestore
from jobhandler import constants


class Template():

    def __init__(self, template_id):
        self.template_id = template_id
        self.template_file_name = constants.TEMPLATE_FILE
        self.template = filestore.get_json(template_id, self.template_file_name)

    def get_template(self):
        return self.template

    @staticmethod
    def load_default_profile():
        # New template id
        template_id = os.urandom(4).encode('hex')
        json_data = json.load(open(os.path.join(os.path.dirname(
            os.path.realpath(__file__)), 'samples', constants.SAMPLE_TEMPLATE_NAME)))
        filestore.create_json(template_id, json_data, constants.TEMPLATE_FILE)
        return template_id

    def add_tag(self, tags=[]):
        tags_add = []
        for tag in tags:
            if tag not in self.template.get(constants.TAGS):
                self.template.get(constants.TAGS).append(tag)
        filestore.put_json(self.template_id, self.template,
                           self.template_file_name)

    def add_nodes(self, nodes=[]):
        node_add = []
        for node in nodes:
            if node not in self.template.get(constants.NODE_LIST):
                self.template.get(constants.NODE_LIST).append(node)
        filestore.put_json(self.template_id, self.template,
                           self.template_file_name)


if __name__ == '__main__':

    print os.path.join(os.path.dirname(os.path.realpath(__file__)), 'samples', constants.SAMPLE_TEMPLATE_NAME)
