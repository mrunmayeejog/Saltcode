import json
from kafka import KafkaClient
import os
import sys
sys.path.append(os.getcwd())

#User defined imports
from collector.collector_manager import CollectorManager
from orchestrator.logger.plugin import FluentdPluginManager
from const import *
from jobhandler.utils import filestore
from poller.pollerm import PollerManager


class PollerTemp:
    template = {}
    pm = PollerManager()

    def __init__(self, temp={}):
        self.template = temp
        self.pm.__init__(temp)

    def set_poller_temp(self, temp):
        self.template = temp[POLLER]
        self.pm.template = temp[POLLER]

    def get_template(self):
        return self.template

    def update_plugin_interval(self, plugin_name, interval, sub_op):
        #update  plugin tag sub_op = "add/delete/update"
        dirty_list = []
        for item in self.template[PLUGINS]:
            if item[NAME] == plugin_name:
                if sub_op == ADD or sub_op == UPDATE:
                    item[INTERVAL] = interval
                if sub_op == DELETE:
                    print ("Delete not supported")
                dirty_list.append(plugin_name)
                self.update(dirty_list)
                break

    def update_plugin_tag(self, plugin_name, tag, sub_op):
        #update collector plugin tag sub_op = "add/delete/update"
        dirty_list = []
        for item in self.template[PLUGINS]:
            if item[NAME] == plugin_name:
                if sub_op == ADD or sub_op == UPDATE:
                    if not TAG in item.keys():
                        item.update({TAG: [tag]})
                    else:
                        item[TAG].append(tag)
                if sub_op == DELETE:
                    if tag in item[TAG]:
                        item[TAG].remove(tag)
                dirty_list.append(plugin_name)
                self.update(dirty_list)
                print item
                break

    def update_plugin_targets(self, plugin_name, target, sub_op):
        #update collector plugin tag sub_op = "add/delete/update"
        dirty_list = []
        for item in self.template[PLUGINS]:
            if item[NAME] == plugin_name:
                if sub_op == ADD or sub_op == UPDATE:
                    if not TARGETS in item.keys():
                        item.update({TARGETS: target})
                    else:
                        item[TARGETS].append(target)
                if sub_op == DELETE:
                    if tag in item[TAG]:
                        item[TARGETS].remove(target)
                dirty_list.append(plugin_name)
                self.update(dirty_list)
                print item
                break

    def add_plugin(self, plugin):
        #add poller plugin
        dirty_list = []
        self.template[PLUGINS].append(plugin)
        dirty_list.append(plugin[NAME])
        self.start(dirty_list)

    def delete_plugin(self, plugin_name):
        #delete poller plugin
        dirty_list = []
        temp = self.template[PLUGINS]
        for item in temp:
            if item[NAME] == plugin_name:
                dirty_list.append(plugin_name)
                self.stop(dirty_list)
                self.template[PLUGINS].remove(item)
                break

    def add_target(self, target):
        #add poller plugin in collector subtemplate
        dirty_list = []
        self.template[TARGETS].append(target)
        dirty_list.append(target[NAME])
        self.start(template, dirty_list)

    def delete_target(self, target_name):
        #delete poller plugin in collector subtemplate
        dirty_list = []
        temp = self.template[TARGETS]
        for item in temp:
            if item[NAME] == target_name:
                dirty_list.append(target_name)
                self.stop(template, dirty_list)
                self.template[TARGETS].remove(item)
                break

    def update_target_meta(self, target_name, meta):
        #update poller meta
        dirty_list = []
        for item in self.template[TARGETS]:
            if item[NAME] == target_name:
                dirty_list.append(target_name)
                item[META] = meta
                self.update(dirty_list)
                break

    def update_plugin_meta(self, plugin_name, meta):
        #update poller meta
        dirty_list = []
        for item in self.template[PLUGINS]:
            if item[NAME] == plugin_name:
                dirty_list.append(plugin_name)
                item[META] = meta
                self.update(dirty_list)
                break

    def get_kafka_details(self):
        details = []
        for item in self.template[TARGETS]:
            if item[TYPE] == KAFKA:
                details.append(item[META])
        return details

    def get_es_details(self):
        details = []
        for item in self.template[TARGETS]:
            if item[TYPE] == ES:
                details.append(item[META])
        return details

    def provision(self):
        print "Deploying poller controller"
        self.pm.deploy()

    def start(self, dirty_list=[]):
        self.pm.start({POLLER: self.template}, dirty_list)

    def update(self, dirty_list=[]):
        print self.template
        self.pm.update({POLLER: self.template}, dirty_list)

    def teardown(self):
        self.pm.teardown(self.template)

    def stop(self, dirty_list=[]):
        self.pm.stop({POLLER: self.template}, dirty_list)


class LoggerTemp:

    template = {}
    #lm = FluentdPluginManager()

    def __init__(self, template={}):
        self.template = template

    def get_template(self):
        return self.template

    def update_interval(self, interval):
        #update node list in collectors and loggers
        self.template[INTERVAL] = interval

    def update_plugin_interval(self, plugin_name, interval, sub_op):
        #update  plugin tag sub_op = "add/delete/update"
        for item in self.template[PLUGINS]:
            if item[TYPE] == plugin_name:
                if sub_op == ADD or sub_op == UPDATE:
                    item[INTERVAL] = interval
                if sub_op == DELETE:
                    if tag in item[TAG]:
                        item[TAG].remove(tag)
                print item

    def update_plugin_filter_level(self, plugin_name, level, sub_op):
        #update filter level in logger plugin sub_op = "add/delete/update"
        for item in self.template[PLUGINS]:
            if item[TYPE] == plugin_name:
                if sub_op == ADD or sub_op == UPDATE:
                    item[FILTER][LEVEL].append(level)
                if sub_op == DELETE:
                    if level in item[FILTER][LEVEL]:
                        item[FILTER][LEVEL].append(level)
                print item

    def update_plugin_tag(self, plugin_name, tag, sub_op):
        #update collector plugin tag sub_op = "add/delete/update"
        for item in self.template[PLUGINS]:
            if item[TYPE] == plugin_name:
                if sub_op == ADD or sub_op == UPDATE:
                    if not TAG in item.keys():
                        item.update({TAG: [tag]})
                    else:
                        item[TAG].append(tag)
                if sub_op == DELETE:
                    if tag in item[TAG]:
                        item[TAG].remove(tag)
                print item

    def add_plugin(self, plugin):
        #add collector plugin in collector subtemplate
	if 'filter' not in plugin.keys():
            plugin['filter'] = {"level": [ "ALL" ]}

        self.template[PLUGINS].append(plugin)
	
    def delete_plugin(self, plugin_name):
        #delete collector plugin in collector subtemplate
        temp = self.template[PLUGINS]
        for item in temp:
            if item[TYPE] == plugin_name:
                self.template[PLUGINS].remove(item)
                break

    def get_kafka_details(self):
        details = []
        for item in self.template[TARGETS]:
            if item[TYPE] == KAFKA:
                details.append(item)
        return details

    def get_es_details(self):
        details = []
        for item in self.template[TARGETS]:
            if item[TYPE] == ES:
                details.append(item)
        return details

    def deploy(self, tags, node_list, op, plugin_name=""):
        if op == START:
            state = True
        if op == STOP:
            state = False

        temp = dict(self.template)
        if not plugin_name:
            temp[ENABLE] = state
        else:
            for item in temp[PLUGINS]:
                if item[TYPE] == plugin_name:
                    item[ENABLE] = state
        #self.lm.deploy({TAG:tags, NODE_LIST:node_list, LOGGERS:temp})
        logger_obj = FluentdPluginManager(temp, tags, node_list)
        logger_obj.deploy(op)

    def teardown(self):
        temp = dict(self.template)
        logger_obj = FluentdPluginManager(temp)
        logger_obj.teardown()


class CollectorTemp:

    template = {}
    cm = CollectorManager()

    def __init__(self, template={}):
        self.template = template

    def get_template(self):
        return self.template

    def update_interval(self, interval):
        #update node list in collectors and loggers
        self.template[INTERVAL] = interval

    def update_plugin_interval(self, plugin_name, interval, sub_op):
        #update  plugin tag sub_op = "add/delete/update"
        for item in self.template[PLUGINS]:
            if item[NAME] == plugin_name:
                if sub_op == ADD or sub_op == UPDATE:
                    item[INTERVAL] = interval
                if sub_op == DELETE:
                    if tag in item[TAG]:
                        item[TAG].remove(tag)
                print item

    def update_plugin_filter_level(self, plugin_name, level, sub_op):
        #update filter level in logger plugin sub_op = "add/delete/update"
        for item in self.template[PLUGINS]:
            if item[NAME] == plugin_name:
                if sub_op == ADD or sub_op == UPDATE:
                    item[FILTER][LEVEL].append(level)
                if sub_op == DELETE:
                    if level in item[FILTER][LEVEL]:
                        item[FILTER][LEVEL].append(level)

    def update_plugin_tag(self, plugin_name, tag, sub_op):
        #update collector plugin tag sub_op = "add/delete/update"
        for item in self.template[PLUGINS]:
            if item[NAME] == plugin_name:
                if sub_op == ADD or sub_op == UPDATE:
                    if not TAG in item.keys():
                        item.update({TAG: [tag]})
                    else:
                        item[TAG].append(tag)
                if sub_op == DELETE:
                    if tag in item[TAG]:
                        item[TAG].remove(tag)
                print item

    def get_es_details(self):
        details = []
        for item in self.template[TARGETS]:
            if item[TYPE] == ES:
                details.append(item)
        return details

    def get_kafka_details(self):
        details = []
        for item in self.template[TARGETS]:
            if item[TYPE] == KAFKA:
                details.append(item)
        return details

    def add_plugin(self, plugin):
        #add collector plugin in collector subtemplate
        self.template[PLUGINS].append(plugin)

    def delete_plugin(self, plugin_name):
        #delete collector plugin in collector subtemplate
        temp = self.template[PLUGINS]
        for item in temp:
            if item[NAME] == plugin_name:
                self.template[PLUGINS].remove(item)
                break

    def provision(self, node_list):
        return True

    def teardown(self, node_list):
        temp = dict(self.template)
        temp[ENABLE] = False
        self.cm.deploy({TAG: [], NODE_LIST: node_list, COLLECTORS: temp})


    def deploy(self, tags, node_list, op, plugin_name=""):
        if op == START:
            state = True
        if op == STOP:
            state = False

        temp = dict(self.template)
        if not plugin_name:
            temp[ENABLE] = state
        else:
            for item in temp[PLUGINS]:
                if item[NAME] == plugin_name:
                    item[ENABLE] = state
        self.cm.deploy({TAG: tags, NODE_LIST: node_list, COLLECTORS: temp})


class SubTemp:

    subtemplate = {}
    subtemplate_name = ""
    node_list = []
    collector_temp = CollectorTemp()
    logger_temp = LoggerTemp()

    def __init__(self, subtemplate_name, subtemplate={}):
        self.subtemplate = subtemplate
        self.subtemplate_name = subtemplate_name
        if self.subtemplate.get(LOGGERS):
            self.logger_temp.__init__(self.subtemplate[LOGGERS])
        if self.subtemplate.get(COLLECTORS):
            self.collector_temp.__init__(self.subtemplate[COLLECTORS])
        self.node_list = self.subtemplate[NODE_LIST]

    def get_template(self):
        temp = {NAME: self.subtemplate_name,
                NODE_LIST: self.node_list,
                COLLECTORS: self.collector_temp.get_template(),
                LOGGERS: self.logger_temp.get_template()}
        return temp

    def update_node_list(self, node, sub_op):
        #update node list for collectors and loggers
        if sub_op == ADD or sub_op == UPDATE:
            if not NODE_LIST in self.subtemplate.keys():
                self.update({NODE_LIST: [node]})
            else:
                self.node_list.append(node)
        if sub_op == DELETE:
            if node in self.node_list:
                self.node_list.remove(node)
        print self.node_list

    def provision_subtemp(self):
        self.collector_temp.provision(self.node_list)
        #self.logger_temp.provision(self.node_list)

    def teardown_subtemp(self):
        self.collector_temp.teardown(self.node_list)
        self.logger_temp.teardown()

    def operate_subtemp(self, op, tags=[], op_level="", plugin_name=""):
        if not op_level:
            self.collector_temp.deploy(tags, self.node_list, op)
            self.logger_temp.deploy(tags, self.node_list, op)
        else:
            if op_level == COLLECTORS:
                self.collector_temp.deploy(tags, self.node_list, op,
                                           plugin_name=plugin_name)
            if op_level == LOGGERS:
                self.logger_temp.deploy(tags, self.node_list, op,
                                        plugin_name=plugin_name)

    def get_kafka_details(self):
        details = {}
        details.update({COLLECTORS: self.collector_temp.get_kafka_details()})
        details.update({LOGGERS: self.logger_temp.get_kafka_details()})
        return details

    def get_es_details(self):
        details = {}
        details.update({COLLECTORS: self.collector_temp.get_es_details()})
        details.update({LOGGERS: self.logger_temp.get_es_details()})
        return details


class Template:
    template = {}
    template_id = ""
    template_name = ""
    tags = []
    subtemp = []
    kafka_details = {}
    es_details = {}
    poller_temp = PollerTemp()

    def init_template(self, template_id="", template=None):
        if template_id:
            self.template = self.get_template_stored(template_id)
            self.template_id = template_id
            self.template_name = self.template[NAME]
        else:
            self.template = template
            self.template_id = os.urandom(4).encode('hex')
        #set components
        self.template_name = self.template[NAME]
        self.tags = self.template[TAG]
        self.poller_temp.set_poller_temp(self.template)
        for item in self.template[SUB_TEMPLATE]:
            subtemp_obj = SubTemp(item[NAME], item)
            self.subtemp.append(subtemp_obj)
        self.save_template()
        return self.template_id

    def build_data_path(self):
        #Nothing to do here for kafka
        #auto.create.topics.enable is True
        '''
        details = self.kafka_details
        if details:
            for subtemp in details[SUB_TEMPLATE]:
                for item in subtemp[COLLECTORS]:
                    client = "%s:%s" % (item[HOST], item[PORT])
                    kclient = KafkaClient(client)
                    for topic in item[TOPIC]:
                        kclient.ensure_topic_exists(topic)
                for item in subtemp[COLLECTORS]:
                    client = "%s:%s" % (item[HOST], item[PORT])
                    kclient = KafkaClient(client)
                    for topic in item[TOPIC]:
                        kclient.ensure_topic_exists(topic)
            for item in details[POLLER]:
                client = "%s:%s" % (item[HOST], item[PORT])
                kclient = KafkaClient(client)
                kclient.ensure_topic_exists(item[TOPIC])
        '''
        #Nothing to do here for elasticsearch
        #Index are auto created
        '''
        details = self.es_details
        if details:
            for subtemp in details[SUB_TEMPLATE]:
                for item in subtemp[COLLECTORS]:
                    client = "%s:%s" % (item[HOST], item[PORT])
                    for index in item[INDEX]:
                        kclient.ensure_topic_exists(topic)
                for item in subtemp[COLLECTORS]:
                    client = "%s:%s" % (item[HOST], item[PORT])
                    for index in item[INDEX]:
                        kclient.ensure_topic_exists(topic)
            for item in details[POLLER]:
                client = "%s:%s" % (item[HOST], item[PORT])
        '''
        pass

    def get_kafka_details(self):
        subtemp_kd = []
        for item in self.subtemp:
            subtemp_kd.append(item.get_kafka_details())
        self.kafka_details.update({SUB_TEMPLATE: subtemp_kd})
        self.kafka_details.update({POLLER:
                                   self.poller_temp.get_kafka_details()})
        return self.kafka_details

    def get_es_details(self):
        subtemp_esd = []
        for item in self.subtemp:
            subtemp_esd.append(item.get_es_details())
        self.es_details.update({SUB_TEMPLATE: subtemp_esd})
        self.es_details.update({POLLER: self.poller_temp.get_es_details()})
        return self.es_details

    def get_template(self):
        subtemp = []
        for item in self.subtemp:
            subtemp.append(item.get_template())
        temp = {NAME: self.template_name, TAG: self.tags,
                SUB_TEMPLATE: subtemp,
                POLLER: self.poller_temp.get_template()}
        return temp

    def save_template(self):
        #save template to db
        #filestore.put_json(self.template_id,
                            #self.template, self.template_name)
        file_path = os.path.join(os.getcwd(), "orchestrator",
                                 TEMPLATE_FILE_PATH, self.template_id)
        temp = self.get_template()
        with open(file_path, 'w') as fh:
            fh.write(json.dumps(temp, indent=4))

    def get_template_stored(self, template_id):
        #fetch template from db
        #return filestore.get_json(self.template_id, self.template_name)
        file_path = os.path.join(os.getcwd(), "orchestrator",
                                 TEMPLATE_FILE_PATH, template_id)
        with open(file_path, 'r') as fh:
            return (json.load(fh))

    #template operations
    def update_tag(self, tag, sub_op):
        if sub_op == ADD or sub_op == UPDATE:
            if tag not in self.tags:
                self.tags.append(tag)
        if sub_op == DELETE:
            if tag in self.tags:
                self.tags.remove(tag)

    def clear_tag(self):
        self.tags = []

    #Subtemplate operations
    def update_subtemplate_node_list(self, subtemp_name, node, sub_op):
        for item in self.subtemp:
            if item.subtemplate_name == subtemp_name:
                item.update_node_list(node, sub_op)
        self.save_template()

    #Collector operations
    def add_collector_plugin(self, subtemp_name, plugin):
        for item in self.subtemp:
            if item.subtemplate_name == subtemp_name:
                item.logger_temp.add_plugin(plugin)
        self.save_template()

    def delete_collector_plugin(self, subtemp_name, plugin_name):
        for item in self.subtemp:
            if item.subtemplate_name == subtemp_name:
                item.logger_temp.delete_plugin(plugin_name)
        self.save_template()

    def update_collector_interval(self, subtemp_name, interval):
        for item in self.subtemp:
            if item.subtemplate_name == subtemp_name:
                item.collector_temp.update_interval(interval)
        self.save_template()

    def update_collector_plugin_interval(self, subtemp_name, plugin_name,
                                         interval, sub_op):
        for item in self.subtemp:
            if item.subtemplate_name == subtemp_name:
                item.collector_temp.update_plugin_interval(plugin_name,
                                                           interval, sub_op)
        self.save_template()

    def update_collector_plugin_tag(self, subtemp_name, plugin_name,
                                    tag, sub_op):
        for item in self.subtemp:
            if item.subtemplate_name == subtemp_name:
                item.collector_temp.update_plugin_tag(plugin_name, tag, sub_op)
        self.save_template()

    #Logger operations
    def add_logger_plugin(self,subtemp_name , plugin):
	for p_plugin in plugin:	
	    p_plugin = json.loads(p_plugin)
            for item in self.subtemp:
                if item.subtemplate_name == subtemp_name:
                    item.logger_temp.add_plugin(p_plugin)
        self.save_template()

    def delete_logger_plugin(self, subtemp_name, plugin ):
	for p_plugin in plugin:
            for item in self.subtemp:
                if item.subtemplate_name == subtemp_name:
                    item.logger_temp.delete_plugin(p_plugin)
        self.save_template()
	
    def update_logger_interval(self, subtemp_name, interval):
        for item in self.subtemp:
            if item.subtemplate_name == subtemp_name:
                item.logger_temp.update_interval(interval)

        self.save_template()

    def update_logger_plugin_interval(self, subtemp_name, plugin_name,
                                      interval, sub_op):
        for item in self.subtemp:
            if item.subtemplate_name == subtemp_name:
                item.logger_temp.update_plugin_interval(plugin_name,
                                                        interval, sub_op)
	
        self.save_template()

    def update_logger_plugin_tag(self, subtemp_name, plugin_name, tag, sub_op):
        for item in self.subtemp:
            if item.subtemplate_name == subtemp_name:
                item.logger_temp.update_plugin_tag(plugin_name, tag, sub_op)
	
        self.save_template()

    def update_logger_plugin_filter_level(self, subtemp_name, plugin_name,
                                          level, sub_op):
        for item in self.subtemp:
            if item.subtemplate_name == subtemp_name:
                item.logger_temp.update_plugin_filter_level(plugin_name,
                                                            level, sub_op)
	
        self.save_template()

    #Poller operations
    def add_poller_target(self, target):
        self.poller_temp.add_target(target)
        self.save_template()

    def delete_poller_target(self, target_name):
        self.poller_temp.delete_target(target_name)
        self.save_template()

    def add_poller_plugin(self, plugin):
        self.poller_temp.add_plugin(plugin)
        self.save_template()

    def delete_poller_plugin(self, plugin_name):
        self.poller_temp.delete_plugin(plugin_name)
        self.save_template()

    def update_poller_target_meta(self, target_name, meta):
        self.poller_temp.update_target_meta(target_name, meta)
        self.save_template()

    def update_poller_plugin_interval(self, plugin_name, interval, sub_op):
        self.poller_temp.update_plugin_interval(plugin_name,
                                                interval, sub_op)
        self.save_template()

    def update_poller_plugin_tag(self, plugin_name, tag, sub_op):
        self.poller_temp.update_plugin_tag(plugin_name, tag, sub_op)
        self.save_template()

    def update_poller_plugin_target(self, plugin_name, target, sub_op):
        self.poller_temp.update_plugin_targets(plugin_name, target, sub_op)
        self.save_template()

    def update_poller_plugin_meta(self, plugin_name, meta):
        self.poller_temp.update_plugin_meta(plugin_name, meta)
        self.save_template()

    #Exec operations
    def deploy_template(self):
        #make calls to provision of all modules (collector/logger/plugin)
        for item in self.subtemp:
            item.provision_subtemp()
        self.poller_temp.provision()

    def deploy_template_poller(self):
        #make calls to provision of poller)
        self.poller_temp.provision()

    def teardown_template(self):
        #pull down whole monitoring infra
        for item in self.subtemp:
            item.teardown_subtemp()
        self.poller_temp.teardown()

    def teardown_template_poller(self):
        #pull down poller
        self.poller_temp.teardown()

    def stop_template(self):
        #make calls to start of all modules (collector/logger/plugin)
        for item in self.subtemp:
            item.operate_subtemp(STOP)
        self.poller_temp.teardown()

    def stop_template_poller(self):
        #pull down poller
        self.poller_temp.teardown()

    def start_template(self):
        #make calls to start of all modules (collector/logger/plugin)
        for item in self.subtemp:
            item.operate_subtemp(START, tags=self.tags)
        self.poller_temp.start()

    def start_template_poller(self):
        #make calls to start of poller
        self.poller_temp.start()

    def deploy_subtemplate(self, subtemp_name="", op_level="", plugin_name=""):
        #make calls to start of all modules (collector/logger)
        for item in self.subtemp:
            if item.subtemplate_name == subtemp_name:
                item.operate_subtemp(START, tags=self.tags, op_level=op_level,
                                     plugin_name=plugin_name)

    def start_subtemplate(self, subtemp_name="", op_level="", plugin_name=""):
        #make calls to start of all modules (collector/logger)
        for item in self.subtemp:
            if item.subtemplate_name == subtemp_name:
                item.operate_subtemp(START, tags=self.tags, op_level=op_level,
                                     plugin_name=plugin_name)

    def stop_subtemplate(self, subtemp_name="", op_level="", plugin_name=""):
        #make calls to start of all modules (collector/logger)
        for item in self.subtemp:
            if item.subtemplate_name == subtemp_name:
                item.operate_subtemp(STOP, tags=self.tags, op_level=op_level,
                                     plugin_name=plugin_name)

    def get_template_status(self):
        #call get status of all modules or fetch from db
        print ""
        '''
        for item in self.subtemp:
            item.check_status_subtemp)
        self.poller_temp.check_status()
        '''
