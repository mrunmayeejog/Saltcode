import json
import os
from base_monitor import *
from template.views import Template
from django.http import HttpResponse, HttpResponseBadRequest
from deepInsight.util import get_logger
from django.conf import settings


class ClusterMonitor:
    logger = get_logger('ClusterMonitor')

    def __init__(self):
        pass

    @classmethod
    def monitor(self, request, tid, oper):
        self.logger.info('API Call - Start Monitoring.')
        self.logger.debug('Input template id - %s', tid)

        response = dict()
        x_temp = Template.objects.filter(id=tid)
        if len(x_temp) == 0:
            response['status'] = 'Template Not Found.'
            self.logger.error('Template Not Found')
            return HttpResponseBadRequest(json.dumps(response))

        template = {}
        with open(settings.DATA_DIR + os.path.sep + tid) as f:
            template = json.load(f)
        sub_templates = [key for key, val in template.get('sub_template')[0].iteritems() if key != 'name' ]
        self.logger.debug('Available sub-templates in template - %s', str(sub_templates))

        watchdogs = {}
        for watchdog_class in BaseMonitor.__subclasses__():
            watcher = watchdog_class(tid)

            name = watcher.get_name()
            if name in sub_templates:
                watchdogs[name] = watcher
            else:
                self.logger.debug('%s - Not available in Template', name)

        # Provision the Template for each of the watch dogs.
        self.logger.debug('Monitoring to start for : %s', str(watchdogs.keys()))
        for name, obj in watchdogs.iteritems():
            status = obj.deploy(oper.upper())
            status = {'a': 'b'}
            self.logger.debug('%s: Provision Status: %s'%(name, json.dumps(status)))

        # Update template status as Active.
        x_temp[0].state = 'Active'
        x_temp[0].save()
        self.logger.info("Template state changed to Active.")

        # Create Response
        response = dict()
        response["Status"] = "Monitoring Started Successfully"
        response["template_id"] = tid
        self.logger.info("Hadoop Monitoring Started Successfully.")
        return HttpResponse(json.dumps(response))

