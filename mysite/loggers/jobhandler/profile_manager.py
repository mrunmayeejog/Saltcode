from orchestrator import orch
from jobhandler import constants
from orchestrator import const

def set_idle_profile(template_id):
    template = None
    try:
        template = orch.get_template_obj(template_id=template_id)
        if template:
            template.clear_tag()
    
            # update linux_static interval to 60 min for idle profile
            template.update_collector_plugin_interval(constants.ALL_NODE_SUBTEMPLATE,
                                                      const.LS,
                                                      60*60, # 60mins
                                                      const.ADD)
            
            # update linux_dynamic interval to 5 min for idle profile
            template.update_collector_plugin_interval(constants.ALL_NODE_SUBTEMPLATE,
                                                      const.LD,
                                                      5*60, # 5mins
                                                      const.ADD)
                            
            template.update_poller_plugin_interval(constants.MAPR_CLUSTER,
                                                   5*60,#5mins
                                                   const.ADD)
            template.save_template()
    except Exception as exception:
        # log.exception("Failed to upload template")
        raise Exception("Exception is setting IDLE profile: {}".format(str(exception)))
        
        
def set_active_profile(template_id):
    template = None
    try:
        template = orch.get_template_obj(template_id=template_id)
        if template:
            template.clear_tag()
    
            # update linux_static interval to 60 min for idle profile
            template.update_collector_plugin_interval(constants.ALL_NODE_SUBTEMPLATE,
                                                      constants.LS,
                                                      60*60, # 60mins
                                                      const.ADD)
            
            # update linux_static interval to 5 min for idle profile
            template.update_collector_plugin_interval(constants.ALL_NODE_SUBTEMPLATE,
                                                      constants.LD,
                                                      30, # 5mins
                                                      const.ADD)
                            
            template.update_poller_plugin_interval(constants.MAPR_CLUSTER,
                                                   30,#5mins
                                                   const.ADD)
            template.save_template()
    except Exception as exception:
        # log.exception("Failed to upload template")
        raise Exception("Exception is setting IDLE profile: {}".format(str(exception)))