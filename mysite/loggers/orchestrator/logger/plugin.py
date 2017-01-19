import sys
import os
import json
from loggers.orchestrator.salt_manager import *
from loggers.orchestrator.const import *


class FluentdPluginManager():

    def __init__(self, template_data, tags=[], node_list=[]):
        # Initialize defaults
        self.plugin_path = os.path.sep + 'etc' + os.path.sep + 'td-agent'
        self.service_name = 'td-agent'
        self.tags, self.plugins, self.target = [], [], []

        self.tags = tags
        self.nodelist = node_list
        self.logger_user_input = template_data

        config_file = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), 'plugin_config.json')

        with open(config_file, 'r') as f:
            self.plugin_config = json.load(f)

        self.plugin_post_data, self.status = [], {}


    def start(self):
        self.change_service_status("start")


    def restart(self):
        self.change_service_status("restart")


    def stop(self):
        self.change_service_status("stop")


    def teardown(self):
        self.change_service_status("stop")


    def check_status(self):
        return self.status


    def change_service_status(self, operation):
        try:
            salt_obj = SaltManager()
            salt_status = salt_obj.change_service_status(self.nodelist, [self.service_name], operation)

            for node in self.nodelist:
                if node not in self.status.keys():
                    self.status[node] = {}
                self.status[node]['minion'] = "Off"
                self.status[node]['fluentd'] = "Off"

            for node in self.nodelist:
                if node in salt_status:
                    self.status[node]['minion'] = "On"
                    if salt_status[node]:
                        self.status[node]['fluentd'] = "on"

        except Exception as e:
            print e


    def configure_plugin_data(self):
        # Read template config, merge them with plugin config and generate plugin params
        for x_plugin in self.logger_user_input.get('plugins'):
            temp = dict()
            temp['source'] = {}
            temp['source']['tag'] = x_plugin.get('tag')
            temp['name'] = x_plugin.get('type')

            if x_plugin.get('type') in self.plugin_config.keys():
                temp['source'].update(self.plugin_config.get(x_plugin.get('type')).get('source'))
                temp['filter'] = self.plugin_config.get(x_plugin.get('type')).get('filter')
                temp['match'] = self.plugin_config.get(x_plugin.get('type')).get('match')
            else:
                print'In-Valid plugin type - ', x_plugin.get('type')
                continue

            filter_lower = [x.lower() for x in x_plugin.get('filter').get('level')]
            filter_upper = [x.upper() for x in x_plugin.get('filter').get('level')]
            if 'all' in filter_lower:
                temp['source']['format'] = 'none'
                temp['usr_filter'] = '(.*?)'
            else:
                temp['source']['format'] = 'none'
                temp['usr_filter'] = '(.*(' + '|'.join(filter_upper) + ').*?)'

            self.plugins.append(temp)
        return True


    def configure_plugin_file(self, data):
        # Add source.
        lines = ['<source>']
        for key, val in data.get('source', {}).iteritems():
            lines.append('\t' + key + ' ' + val)
        lines.append('</source>')

        # Add grep filter.
        lines.append('\n<filter ' + data.get('source').get('tag') + '>')
        lines.append('\t@type grep')
        lines.append('\tregexp1 message ' + data.get('usr_filter'))
        lines.append('</filter>')

        # Add record-transormation filter.
        lines.append('\n<filter ' + data.get('source').get('tag') + '>')
        lines.extend(['\t@type record_transformer','\t<record>'])
        for key, val in data.get('filter', {}).iteritems():
            lines.append('\t\t' + key + ' \"' + val + '\"')
        
        # lines.append('\t\ttags ' + str(self.tags + [data.get('source').get('tag')]))
        tags = [ str(x) for x in self.tags + [data.get('source').get('tag')]]
        lines.append('\t\ttags ' + str(tags).replace('\'', '"'))
        lines.extend(['\t</record>', '</filter>'])

        # Add match.
        if data.get('match').has_key('tag'):
            lines.append('\n<match '+ data.get('match').get('tag') + '>')
            data.get('match').pop('tag')
        else:
            lines.append('\n<match '+ data.get('source').get('tag') + '>')

        for key, val in self.logger_user_input.get('target')[0].iteritems():
            if key == "type":
                key = "@" + key
            lines.append('\t' + key + ' ' + val)

        for key, val in data.get('match', {}).iteritems():
            lines.append('\t' + key + ' ' + val)
        lines.append('</match>')

        filename = self.plugin_path + os.path.sep + data.get('name')
        self.plugin_post_data.append((filename, '\n'.join(lines)))
        return True


    def generate_plugins(self):
        # Generate the files in the salt dir
        self.configure_plugin_data()

        for x_plugin in self.plugins:
            self.configure_plugin_file(x_plugin)
        return True


    def generate_fluentd_config_file(self):
        lines = []
        for x_plugin in self.plugins:
            lines.append('@include ' + x_plugin.get('name'))

        lines.append('\n<match *>')
        for key, val in self.logger_user_input.get('target')[0].iteritems():
            if key == "type":
                key = "@" + key
            lines.append('\t' + key + ' ' + val)

        lines.append('\t' + 'flush_interval' + ' ' + self.plugin_config.get('default_flush_interval'))
        lines.append('\t' + 'include_tag_key' + ' true')
        lines.append('</match>')

        filename =  self.plugin_path + os.path.sep + 'td-agent.conf'
        self.plugin_post_data.append((filename, '\n'.join(lines)))
        return True


    def deploy(self, oper):

        salt_obj = SaltManager()
	status = {}
        if oper == START:
            if self.logger_user_input.get('enable', False):
		print self.logger_user_input
		raw_input()
                self.generate_plugins()
                self.generate_fluentd_config_file()
                print '\nPost Data: ', json.dumps(self.plugin_post_data)
                status = salt_obj.push_config(self.plugin_post_data, self.nodelist)
                self.restart()
            else:
		print "y here"
                self.stop()
            
        elif oper == STOP:
            if self.logger_user_input.get('enable', False):
                disable_files, disable_plugins = [], []
                for x_plugin in self.logger_user_input.get('plugins'):
                    disable_plugins.append(x_plugin.get('type'))
                    disable_files.append(self.plugin_path + os.path.sep + x_plugin.get('type'))

                status = salt_obj.delete_files(disable_files, self.nodelist)
                new_config_data = salt_obj.reset_logger_config(disable_plugins,self.nodelist)
                config_post_data =[[self.plugin_path + os.path.sep + 'td-agent.conf', new_config_data]]
                config_status  = salt_obj.push_config(config_post_data, self.nodelist)
                status.update(config_status)
                self.restart()
            else:
                self.stop

        elif oper == 'teardown':
            self.stop()
            return

        else:
            pass

        for node, plugin_status in status.iteritems():
            if node not in self.status.keys():
                self.status[node] = {}
            self.status[node]['plugins'] = plugin_status        

        print '\nStatus :', json.dumps(self.status)
        return self.status

