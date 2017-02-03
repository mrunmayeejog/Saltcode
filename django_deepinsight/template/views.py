# from django.shortcuts import render
# import django
import json
import os
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Template
from deepInsight.util import get_logger


class TemplateManager:
    __name__ = 'TemplateManager'
    logger = get_logger(__name__)

    def __init__(self, id):
        self.id = id

    @classmethod
    def list(self, request):
        self.logger.info('API Call - List Templates.')
        all_templates = Template.objects.all()

        if not len(all_templates):
            self.logger.debug('Application has no template Added.')

        response = []
        for x_temp in all_templates:
            response.append({"Id": x_temp.id, "State": x_temp.state,
                             "Cluster": x_temp.cluster, "Created": x_temp.created.isoformat()})
        return HttpResponse(json.dumps(response))

    @classmethod
    @csrf_exempt
    def show(self, request, id):
        self.logger.info('API Call - Show Template.')
        x_temp = Template.objects.filter(id=id)

        response = dict()
        if len(x_temp) == 0:
            self.logger.error('Template not found for id - %s.', id)
            response['status'] = 'In-Valid Template-Id.'
            return HttpResponseNotFound(json.dumps(response))
        else:
            with open(settings.DATA_DIR + os.path.sep + id) as f:
                response = json.load(f)
        return HttpResponse(json.dumps(response))

    @classmethod
    @csrf_exempt
    def add(self, request):
        self.logger.info('API Call - Add a new Template.')
        # Read input and update file to temp directory.
        response = dict()
        filedata = request.FILES.get('file', None)

        if not filedata:
            self.logger.error('Invalid input ( file not attached as File-Filedata Key-Value pair ).')
            response['Status'] = 'In-valid input.'
            return HttpResponseBadRequest(json.dumps(response))

	filepath = settings.DATA_DIR + os.path.sep + id
        tid = os.urandom(4).encode('hex')
        destination = open(filepath, 'w')
        for chunk in filedata.chunks():
            destination.write(chunk)
        destination.close()

        filedata, filepath = {}, settings.DATA_DIR + os.path.sep + tid
        try:
            with open(filepath, 'r') as f:
                filedata = json.load(f)
        except:
            self.logger.error('Invalid input ( Not JSON ).')
            os.remove(filepath)
            response['Status'] = 'In-valid input.'
            return HttpResponseBadRequest(json.dumps(response))

        self.logger.debug('Template file successfully Stored.')

        # Update record to the database.
        record = Template()
        record.id, record.state = tid, 'Init'
        record.cluster = filedata.get('name', 'Not Given')
        response['id'] = tid
        record.save()
        self.logger.debug('Template record successfully Added.')
        self.logger.info('Template successfully Added.')
        return HttpResponse(json.dumps(response))

    @classmethod
    def delete(self, request, id):
        self.logger.info('API Call - Delete Template.')
        x_temp = Template.objects.filter(id=id)

        response = dict()
        if len(x_temp) == 0:
            self.logger.error('Template does not exist for id - %s.', id)
            response['status'] = 'In-Valid Template-Id.'
            return HttpResponseNotFound(json.dumps(response))
        else:
            # Delete stored file.
            filepath = settings.DATA_DIR + os.path.sep + id
            if os.path.isfile(filepath):
                os.remove(filepath)
            self.logger.debug('Template file successfully Deleted.')

            # Delete database Record.
            x_temp.delete()
            self.logger.debug('Template file successfully Deleted.')
            self.logger.info('Template successfully Deleted.')
            response['status'] = 'Template Deleted.'
        return HttpResponse(json.dumps(response))
