
# User defined imports
from loggers.orchestrator.collector.collectd_manager import *
from loggers.orchestrator.salt_manager import *
# from salt_manager import *
from loggers.orchestrator.collector.constants import *


class CollectorManager():

    def __init__(self):
        self.template = {}
        self.config_info = []
        self.collector_type = COLLECTD
        self.nodemgr_type = SALT
        self.node_list = []
        self.nodes_state_dict = {}
        self.nodes_cfg_list = []

    def init_template(self, template):
        self.template = template

    def deploy(self, template):
        # print template
        status_dict = {}
        status_dict[CONFIG] = {}
        status_dict[PUSH] = {}
        success = False
        error_msg = ""
        try:
            # if the node_list is empty then just simply return
            if not template[NODES]:
                status_dict[ERROR] = EMPTY_NODE_LIST
                return (success, status_dict)

            '''
            if "collectors" not in template or "enable" not in template["collectors"]:
                status_dict["error_msg"] = ""
                return (success, status_dict)
            '''
            # if the operation is to disable just stop collector and return.
            if not template[COLLECTORS][ENABLED]:
                return self.stop(template)
            collector_obj = self.get_collector_obj(template)
            (success, conf_dict) = collector_obj.generate_config(template)
            # print "generated config"
            # print success, conf_dict
            status_dict[CONFIG][FAILED_LIST] = conf_dict[FAILED_LIST]
            if success:
                nodemgr_obj = self.get_nodemgr_obj(template)
                status_dict[DELETE] = nodemgr_obj.delete_files(file_list=[ALL_CONF],
                                                    dest_nodes=template[NODES])
                status_dict[PUSH] = nodemgr_obj.push_config(conf_dict[SUCCESS_LIST],
                                                    template[NODES])
            # print status_dict
                status_dict[START] = self.start(template)
            else:
                status_dict[CONFIG][ERROR] = conf_dict[ERROR] 
                error_msg = conf_dict[ERROR]
        except KeyError, e:
            error_msg = str(e) + KEY_ERROR
            success = False
            print e
        except Exception as e:
            error_msg = str(e)
            print e
            success = False
        status_dict[ERROR] = error_msg
        return (success, status_dict)

    def start(self, template):
        self.change_service_status(template, RESTART)
        return self.nodes_state_dict

    def stop(self, template):
        self.change_service_status(template, STOP)
        return self.nodes_state_dict

    def teardown(self, template):
        self.change_service_status(template, STOP)
        nodemgr_obj = self.get_nodemgr_obj(template)
        nodemgr_obj.delete_files(file_list=[ALL_CONF], dest_nodes=template[NODES])
        return self.nodes_state_dict

    def check_status(self, template):
        self.change_service_status(template, STATUS)
        return self.nodes_state_dict

    def change_service_status(self, template, operation):
        state_dict = {}
        error_msg = ""
        try:
            nodemgr_obj = self.get_nodemgr_obj(template)
            status = nodemgr_obj.change_service_status(template[NODES],
                                                                     [self.collector_type],
                                                                     operation)
            if operation != STATUS:
                for node in template[NODES]:
                    state_dict[node] = False
            for node in template[NODES]:
                if node in status:
                    state_dict[node] = status[node]
        except KeyError, e:
            error_msg = str(e) + KEY_ERROR
        except Exception as e:
            error_msg = str(e)
        self.nodes_state_dict = state_dict

    def get_nodemgr_obj(self, template):
        if NODEMGR in template:
            if template[NODEMGR] == SALT:
                self.nodemgr_type = SALT
                return SaltManager()

        # default case for now is to return salt mgr object
        self.nodemgr_type = SALT
        return SaltManager()

    def get_collector_obj(self, template):
        if COLLECTOR in template:
            if template[COLLECTOR] == COLLECTD:
                self.collector_type = COLLECTD
                return CollectdManager()

        # default case for now is to return collectd mgr object
        self.collector_type = COLLECTD
        return CollectdManager()


def provision_collector(template):
    # print template
    success = False
    return_dict = {}
    try:
        obj = CollectorManager()
        print obj.deploy(template)
        #print obj.teardown(template)
        # print obj.stop(template)
        # print obj.check_status(template)
        # print obj.nodes_state_dict
    except Exception as e:
        print e
        success = False
    return (success, return_dict)

# import cfg_json
# input_cfg = cfg_json.test_json
# provision_collector(input_cfg)
# start_collector(input_cfg)
