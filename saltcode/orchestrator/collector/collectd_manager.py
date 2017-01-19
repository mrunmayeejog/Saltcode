import os
#from mako.template import Template

# User defined imports
from conf import *
from constants import *


class CollectdManager():

    def __init__(self):
        self.plugin_src_dir = CollectdPluginDestDir
        self.plugin_conf_dir = CollectdPluginConfDir
        self.collectd_conf_dir = CollectdConfDir
        self.interval = 10
        self.cfg_list = []
        self.tag_list = []
        self.target_list = []
        self.seperate_files = True
        self.targets = {}
        self.tags = {}

    def get_dest_filename(self, plugin):
        return os.path.join(self.plugin_src_dir, plugin+EXTSN)

    def set_targetandtag(self, plugin, plugin_targets=[], plugin_tags=[]):
        try:
            # print plugin, targets, tags
            for ptarget in plugin_targets:
                for target in self.target_list:
                    if ptarget == target[NAME]:
                        target_type = target[TYPE]
                        if target_type not in self.targets:
                            self.targets[target_type] = {}
                        if ptarget not in self.targets[target_type]:
                            self.targets[target_type][ptarget] = {CONFIG:target, PLUGINS:[]}
                        self.targets[target_type][ptarget][PLUGINS].append(plugin)
            if plugin_tags:
                self.tags[plugin] = plugin_tags
            return True
        except Exception as e:
            print e
        return False

    def get_section_cfg(self, section_name, section):
        section_cfg = ""
        try:
            filename = section_name + EXTSN
            filename = os.path.join(os.getcwd(), TEMPLATE_DIR, filename)
            mytemplate = Template(filename=filename)
            section_cfg = mytemplate.render(data=section)
            # print section_cfg
            if section_cfg is not None:
                # filters and targets won't have name key
                if NAME in section and TARGETS in section and TAGS in section:
                    if self.set_targetandtag(section[NAME], section[TARGETS], section[TAGS]):
                        return (True, section_cfg)
                else:
                    return (True, section_cfg)
        except KeyError, e:
            print str(e) + KEY_ERROR
        except Exception as e:
            print e
        return (False, None)

    def generate(self):
        return_dict = {}
        return_dict[SUCCESS_LIST] = []
        return_dict[FAILED_LIST] = []
        success_overall = False
        # print cfg_list
        try:
            for cfg in self.cfg_list:
                filename = self.get_dest_filename(cfg[NAME])
                (success, section_cfg) = self.get_section_cfg(cfg[NAME], section=cfg)
                # print success, section_cfg
                if success:
                    return_dict[SUCCESS_LIST].append((filename, section_cfg))
                else:
                    return_dict[FAILED_LIST].append((filename, ERROR_CFG_GEN))
                success_overall = success_overall or success
            # print success_overall, return_dict
            # print self.targets
            for target, conf in self.targets.items():
                filename = self.get_dest_filename(target)
                (success, section_cfg) = self.get_section_cfg(target, section=conf)
                # print success, section_cfg
                if success:
                    return_dict[SUCCESS_LIST].append((filename, section_cfg))
                else:
                    return_dict[FAILED_LIST].append((filename, ERROR_CFG_GEN))
                success_overall = success_overall or success
            # print success_overall, return_dict
            filename = self.get_dest_filename(FILTERS)
            (success, cfg) = self.get_section_cfg(FILTERS, {TAGS: self.tags, TARGETS: self.targets})
            # print success, cfg
            if success:
                return_dict[SUCCESS_LIST].append((filename, cfg))
            else:
                return_dict[FAILED_LIST].append((filename, ERROR_CFG_GEN))
            success_overall = success_overall or success

            return (success_overall, return_dict)
        except KeyError, e:
            print str(e) + KEY_ERROR
        except Exception as e:
            print e
        return_dict[FAILED_LIST].append((DUMMY, DUMMY))
        return (success_overall, return_dict)

    def create_cfg_list(self, template):
        error_msg = ""
        try:
            if TAGS in template:
                self.tag_list = self.tag_list + template[TAGS]
            if COLLECTORS in template:
                collector_dict = template[COLLECTORS]
                if TAGS in collector_dict:
                    self.tag_list = self.tag_list + collector_dict[TAGS]
                if INTERVAL in collector_dict:
                    self.interval = collector_dict[INTERVAL]
                if TARGETS in collector_dict:
                    self.target_list = collector_dict[TARGETS]
                target_names_list = []
                for target in self.target_list:
                    target_names_list.append(target[NAME])
                plugin_cfg_list = []
                plugin_disable_list = []
                if PLUGINS in collector_dict:
                    for plugin in collector_dict[PLUGINS]:
                        if not plugin[ENABLED]:
                            plugin_disable_list.append(plugin)
                            continue
                        if TARGETS not in plugin:
                            plugin[TARGETS] = target_names_list
                        elif not set(plugin[TARGETS]) <= set(target_names_list):
                            error_msg = "Invalid target specified for plugin " + plugin[NAME]
                            return (False, error_msg)
                        if INTERVAL not in plugin:
                            plugin[INTERVAL] = self.interval
                        if TAGS not in plugin:
                            plugin[TAGS] = self.tag_list
                        else:
                            plugin[TAGS] = self.tag_list + plugin[TAGS]
                        plugin_cfg_list.append(plugin)
                    #for target in self.target_list:
                    #    plugin_cfg_list.append(target)
                    # print collector_dict["plugins"]
                    self.cfg_list = plugin_cfg_list
                    # print self.cfg_list
                return (True, error_msg)
        except KeyError, e:
            error_msg = str(e) + KEY_ERROR
            print e
        except Exception as e:
            error_msg = str(e)
            print e
        return (False, error_msg)

    def generate_config(self, template):
        success = False
        return_dict = {}
        return_dict[SUCCESS_LIST] = []
        return_dict[FAILED_LIST] = []
        try:
            # print template
            (success, error_msg) = self.create_cfg_list(template)
            if success:
                (success, return_dict) = self.generate()
                # print success, return_dict
            else:
                return_dict[ERROR] = error_msg
        except Exception as e:
            print e
        return (success, return_dict)

if __name__ == '__main__':
    usage = ('Usage: python cfg_modify.py ' +
                     'parameters_to_be_changed([(section, option_list)]) ' +
                     'file_to_be_modified ' +
                     'validation_required(True|False) ' +
                     'template_file')
    try:
        if len(sys.args) == 5:
            print modify_cfg(sys.argv[1], sys.argv[2], bool(sys.argv[3]), sys.argv[4])
        else:
            print usage
    except Exception as e:
        print usage
        print e
