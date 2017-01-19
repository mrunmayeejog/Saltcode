import os, json
from orchestrator import orch
from jobhandler import constants
from loggers.orchestrator.const import *


class TemplateApp():

    def upload_template(self):
        response = {}
        template_file = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), 'jobhandler','template', 'samples', 'sample_profile_prod_1.json')

        print "Reading Template:",template_file
        template = None
        with open(template_file) as data_file:
            template = json.load(data_file)

        template_obj= orch.Template()
        template_id=template_obj.init_template(template=template)
        response["template_id"] = template_id
        response["template_name"] = template.get('name')
        response["message"] = "Successfully template uploaded "
        return response



    def get_template(self,template_id=''):
	print template_id
        file_path = os.path.join(os.getcwd(), "loggers/orchestrator",
                                 TEMPLATE_FILE_PATH, template_id)
        with open(file_path) as fh:
	    template = json.load(fh)

        template_obj= orch.Template()
        template_id=template_obj.init_template(template=template)
            

	'''
        template_obj = orch.Template()
        template_obj.init_template(template_id=template_id)
        temp = json.dumps(template_obj.get_template(), sort_keys=True,indent=10, separators=(',', ': '))    
	'
	template_obj = orch.get_template_obj(template_id=template_id)
	'''
        return template_obj	

    def start_hadoop_monitoring(self,template_id = ''):
        template_obj = orch.get_template_obj(template_id=template_id)
	try:
            # deploy Poller template
            template_obj.deploy_template()
            # Start Poller template
            template_obj.start_template()
            response["message"] = "Successfully initiated the monitoring"
            response["template_id"] = template_id
            return json.dumps(response)
        except Exception as exception:
            raise Exception("Failed to start the monitoring: {}".format(str(exception)), constants.INTERNAL_SERVER_ERROR)

    def stop_hadoop_monitoring():
        template_obj = orch.get_template_obj(template_id=template_id)
	try:
            # STOP  Poller template
            template_obj.stop_template()
            response["message"] = "Successfully stopped the monitoring"
            response["template_id"] = template_id
            return json.dumps(response)
        except Exception as exception:
            raise Exception("Failed to start the monitoring".format(str(exception)), constants.INTERNAL_SERVER_ERROR)




