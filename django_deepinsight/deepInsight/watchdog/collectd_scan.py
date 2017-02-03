from base_monitor import *
from deepInsight.watchdog.constants import *
from deepInsight.util import get_logger
import copy
from mako.template import Template


class CollectdPluginManager(BaseMonitor):
    _NAME_ = "collectors"

    def __init__(self, tid):
        super(CollectdPluginManager, self).__init__(CollectdPluginManager._NAME_, tid)

        # Initialize logger object
        self.logger = get_logger('CollectdPluginManager')

        self.collector_type = COLLECTD
        self.config_info, self.node_state, self.nodes_cfg_list = [], [], []
        self.all_conf = CollectdPluginDestDir + ALL_CONF

    def get_name(self):
        return self.name

    def deploy(self, oper):
        self.logger.debug("Deploying Collectors")
        status_dict = dict()
        status_dict[CONFIG], status_dict[PUSH] = dict(), dict()
        success = False
        error_msg = ""
        try:
            # if the node_list is empty then just simply return
            if not self.nodelist:
                status_dict[ERROR] = EMPTY_NODE_LIST
                self.logger.error('Node list is Empty.')
                return success, status_dict

            # if the operation is to disable just stop collector and return.
            if not self.sub_template.get(ENABLED):
                self.logger.info("Stopping Collector Service.")
                return self.stop(self.sub_template)

            collector_obj = self.get_collector_obj(self.sub_template)
            self.logger.info("Generating config")

            # Generate config
            success, conf_dict = collector_obj.generate_config(self.sub_template)
            self.logger.debug('Configuration Dictionary: %s', str(conf_dict))
            status_dict[CONFIG][FAILED_LIST] = conf_dict[FAILED_LIST]

            # if config generation is Successful then delete remote conf files.
            # and then push the new conf files and restart service
            if success:
                self.logger.info("Config Generation Completed Successfully")

                # get node manager object
                salt_obj = SaltManager()

                # delete remote conf files
                self.logger.info("deleting remote conf files")
                status_dict[DELETE] = salt_obj.delete_files(file_list=[self.all_conf],
                                                    dest_nodes=self.nodelist)
                self.logger.debug(str(status_dict[DELETE]))

                # push conf files on remote node
                self.logger.info("Pushing config files on Remote Machine")
                status_dict[PUSH] = salt_obj.push_config(conf_dict[SUCCESS_LIST],
                                                    self.nodelist)
                self.logger.debug(str(status_dict[PUSH]))

                # restart service
                self.logger.info("Restarting service")
                status_dict[START] = self.start(self.sub_template)
                self.logger.debug(str(status_dict[START]))
            else:
                status_dict[CONFIG][ERROR] = conf_dict[ERROR]
                error_msg = conf_dict[ERROR]
                self.logger.info("config generation failed")
                self.logger.debug(str(error_msg))
        except KeyError, e:
            error_msg = str(e) + KEY_ERROR
            success = False
            self.logger.error(error_msg)
        except Exception as e:
            error_msg = str(e)
            success = False
            self.logger.error(error_msg)
        status_dict[ERROR] = error_msg
        self.logger.info("Completed deploy")
        self.logger.debug("Deploy return status: " + str(status_dict))
        return success, status_dict

    def start(self):
        self.change_service_status(RESTART)
        return self.node_state

    def stop(self):
        self.change_service_status(STOP)
        return self.node_state

    def teardown(self):
        error_msg = ""
        # first stop service and then delete remote conf files
        try:
            # Stop Service
            self.logger.info("Tearing down / Stopping service.")
            self.change_service_status(STOP)

            # delete remote conf files
            salt_obj = SaltManager()
            self.logger.info("Deleting Remote conf Files.")
            status = salt_obj.delete_files(file_list=[self.all_conf], dest_nodes=self.nodelist)
            self.logger.info("Teardown Complete.")
            self.logger.debug("Teardown Return Status: %s", str(status))
        except Exception as e:
            error_msg += str(e)
            self.logger.error('Exception: %s', error_msg)
        return self.node_state

    def check_status(self):
        self.change_service_status(STATUS)
        return self.node_state

    def change_service_status(self, operation):
        state = []
        error_msg = ""
        try:
            salt_obj = SaltManager()
            status = salt_obj.change_service_status(self.nodelist, [self.collector_type], operation)

            # Iterate over Node List and Update the Status.
            for node in self.nodelist:
                # fill default status to "no response"
                status_temp = {NODE_NAME: node, STATUS: NO_RESP}
                if node in status:
                    # status = True means running
                    if status[node]:
                        status_temp[STATUS] = RUNNING
                    else:
                        status_temp[STATUS] = NOT_RUNNING
                state.append(status_temp)
        except KeyError, e:
            error_msg = str(e) + KEY_ERROR
            self.logger.error('Exception: %s', error_msg)
        except Exception as e:
            error_msg = str(e)
            self.logger.error('Exception: %s', error_msg)
        self.logger.info("Changed service status")
        self.logger.debug('Node State: %s', str(state))
        self.node_state = state

    def get_collector_obj(self, template):
        if COLLECTOR in template:
            if template[COLLECTOR] == COLLECTD:
                self.collector_type = COLLECTD
                return CollectdManager()

        # default case for now is to return collectd mgr object
        self.collector_type = COLLECTD
        self.all_conf = CollectdPluginDestDir + ALL_CONF
        return CollectdManager()


class CollectdManager:

    def __init__(self):
        self.plugin_src_dir = CollectdPluginDestDir
        self.plugin_conf_dir = CollectdPluginConfDir
        self.collectd_conf_dir = CollectdConfDir
        self.interval = 10

        self.cfg_list, self.tag_list, self.target_list = [], [], []
        self.tags, self.targets = {}, {}
        self.seperate_files = True

        self.logger = get_logger(COLLECTD_MGR)

    def get_dest_filename(self, plugin):
        return os.path.join(self.plugin_src_dir, plugin+EXTSN)

    def set_target_and_tag(self, plugin, plugin_targets=[], plugin_tags=[]):
        error_msg = ""
        try:
            self.logger.debug("plugin: " + str(plugin) + " targets: " + str(plugin_targets) + " tags: " + str(plugin_tags))
            for ptarget in plugin_targets:
                for target in self.target_list:
                    if ptarget == target[NAME]:
                        target_type = target[TYPE]
                        if target_type not in self.targets:
                            self.targets[target_type] = {}
                        if ptarget not in self.targets[target_type]:
                            self.targets[target_type][ptarget] = {CONFIG: target, PLUGINS: []}
                        self.targets[target_type][ptarget][PLUGINS].append(plugin)
            if plugin_tags:
                self.tags[plugin] = plugin_tags
            return True
        except Exception as e:
            error_msg += str(e)
        self.logger.error(error_msg)
        return False

    '''
    Input: Plugin name and dictionary of options.
    Output: Returns plugin config.
    '''
    def get_section_cfg(self, section_name, section):
        section_cfg = ""
        error_msg = ""
        try:
            filename = section_name + EXTSN
            filename = os.path.join(os.getcwd(), TEMPLATE_DIR, filename)
            mytemplate = Template(filename=filename)
            section_cfg = mytemplate.render(data=section)
            self.logger.debug(section_cfg)
            if section_cfg is not None:
                # filters and targets won't have name key
                if NAME in section and TARGETS in section and TAGS in section:
                    if self.set_target_and_tag(section[NAME], section[TARGETS], section[TAGS]):
                        return True, section_cfg
                else:
                    return True, section_cfg
        except KeyError, e:
            error_msg = error_msg + str(e) + KEY_ERROR
        except Exception as e:
            error_msg += str(e)
        self.logger.error('Exception: %s', error_msg)
        return False, None

    '''
    Iterates over the list of plugins generating config for each plugin.
    Then iterates over target list and generates config for targets.
    At the end generates config for filters.
    '''
    def generate(self):
        error_msg = ""
        return_dict = dict()
        return_dict[SUCCESS_LIST] = []
        return_dict[FAILED_LIST] = []
        success_overall = False
        self.logger.debug("config_lsit: " + str(self.cfg_list))
        try:
            # generate config for plugins
            for cfg in self.cfg_list:
                filename = self.get_dest_filename(cfg[NAME])
                (success, section_cfg) = self.get_section_cfg(cfg[NAME], section=cfg)
                self.logger.debug("success: " + str(success) + " section_cfg: " + section_cfg)
                if success:
                    self.logger.debug("Generated config for " + cfg[NAME])
                    return_dict[SUCCESS_LIST].append((filename, section_cfg))
                else:
                    self.logger.debug("Config generation failed for " + cfg[NAME])
                    return_dict[FAILED_LIST].append((filename, ERROR_CFG_GEN))
                success_overall = success_overall or success
            self.logger.debug("success_overall: " + str(success) + " plugin config gen status: " + str(return_dict))

            # generate config for targets
            for target, conf in self.targets.items():
                filename = self.get_dest_filename(target)
                (success, section_cfg) = self.get_section_cfg(target, section=conf)
                self.logger.debug("success: " + str(success) + " section_cfg: " + section_cfg)
                if success:
                    self.logger.debug("Generated config for " + target)
                    return_dict[SUCCESS_LIST].append((filename, section_cfg))
                else:
                    self.logger.debug("Config generation failed for " + target)
                    return_dict[FAILED_LIST].append((filename, ERROR_CFG_GEN))
                success_overall = success_overall or success
            self.logger.debug("success_overall: " + str(success) + " plugin and target config gen status: " + str(return_dict))

            # generate config for filters
            filename = self.get_dest_filename(FILTERS)
            (success, cfg) = self.get_section_cfg(FILTERS, {TAGS: self.tags, TARGETS: self.targets})
            self.logger.debug("success: " + str(success) + " section_cfg: " + cfg)
            if success:
                self.logger.debug("Generated config for filters")
                return_dict[SUCCESS_LIST].append((filename, cfg))
            else:
                self.logger.debug("Config generation failed for filters")
                return_dict[FAILED_LIST].append((filename, ERROR_CFG_GEN))
            success_overall = success_overall or success

            self.logger.debug("plugin, target and filter config gen status: " + str(return_dict))
            return success_overall, return_dict
        except KeyError, e:
            error_msg = error_msg + str(e) + KEY_ERROR
        except Exception as e:
            error_msg += str(e)
        return_dict[FAILED_LIST].append((DUMMY, DUMMY))
        self.logger.error(error_msg)
        self.logger.error(str(return_dict[FAILED_LIST]))
        return success_overall, return_dict

    '''
    Input: Template in Orchestrator format.
    Functionality: Applies global level options on individual
                   plugins and sets list of plugins and targets.
    '''
    def create_cfg_list(self, template):
        error_msg = ""
        try:
            if TAGS in template:
                self.tag_list = self.tag_list + list(template[TAGS])
            if COLLECTORS in template:
                collector_dict = template[COLLECTORS]
                if TAGS in collector_dict:
                    self.tag_list = self.tag_list + list(collector_dict[TAGS])
                if INTERVAL in collector_dict:
                    self.interval = collector_dict[INTERVAL]
                if TARGETS in collector_dict:
                    self.target_list = list(collector_dict[TARGETS])
                target_names_list = []
                for target in self.target_list:
                    target_names_list.append(target[NAME])
                plugin_cfg_list = []
                plugin_disable_list = []
                if PLUGINS in collector_dict:
                    for plugin in collector_dict[PLUGINS]:
                        plugin_temp = copy.deepcopy(plugin)
                        if not plugin_temp[ENABLED]:
                            plugin_disable_list.append(plugin_temp)
                            continue
                        if TARGETS not in plugin_temp:
                            plugin_temp[TARGETS] = target_names_list
                        elif not set(plugin_temp[TARGETS]) <= set(target_names_list):
                            error_msg = "Invalid target specified for plugin " + plugin_temp[NAME]
                            self.logger.error(error_msg)
                            return False, error_msg
                        if INTERVAL not in plugin_temp:
                            plugin_temp[INTERVAL] = self.interval
                        if TAGS not in plugin_temp:
                            plugin_temp[TAGS] = self.tag_list
                        else:
                            plugin_temp[TAGS] = self.tag_list + plugin_temp[TAGS]
                        plugin_cfg_list.append(plugin_temp)
                    self.cfg_list = plugin_cfg_list
                self.logger.debug("plugin_list: " + str(plugin_cfg_list))
                return True, error_msg
        except KeyError, e:
            error_msg = str(e) + KEY_ERROR
        except Exception as e:
            error_msg = str(e)
        self.logger.error(error_msg)
        return False, error_msg

    def generate_config(self, template):
        self.logger.debug("In generate_config")
        self.logger.debug("template: ")
        self.logger.debug(str(template))
        success = False
        return_dict = dict()
        return_dict[SUCCESS_LIST] = []
        return_dict[FAILED_LIST] = []
        try:
            self.logger.debug("converting orchestrator input template to collectd format")
            (success, error_msg) = self.create_cfg_list(template)
            if success:
                self.logger.debug("template conversion successfull")
                self.logger.debug("generating config")
                (success, return_dict) = self.generate()
                self.logger.debug("success: " + str(success) + " generate_config return status: " + str(return_dict))
            else:
                return_dict[ERROR] = error_msg
                self.logger.error("template conversion failed")
        except Exception as e:
            self.logger.error(str(e))
        return success, return_dict
