from orchestrator import orch
import json
import os

template_file = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), 'jobhandler','template', 'samples', 'sample_collector.json')

print "Reading Template:",template_file
template = None
with open(template_file) as data_file:
    template = json.load(data_file)

print template
template_obj= orch.Template()
template_id=template_obj.init_template(template=template)

'''
# Call to logger start subtemplate
template_obj.start_subtemplate(subtemp_name="ALL NODES", op_level='loggers')

# Call to logger stop subtemplate
template_obj.stop_subtemplate(subtemp_name="ALL NODES", op_level='loggers')

# Call to logger teardown subtemplate
template_obj.teardown_subtemp()

'''

def add_node_list():
    template_obj.update_subtemplate_node_list("ALL NODES","node117","del")
    print "Updated the node list"

def collector_cpu_plugin():
    template_obj.start_subtemplate(subtemp_name="ALL NODES", op_level='collectors',plugin_name='cpu')
    print "succesfully started collector with CPU plugin"

def collector_cpu_stats_plugin():
    template_obj.start_subtemplate(subtemp_name="ALL NODES", op_level='collectors',plugin_name='cpu_static')
    print "succesfully started collector with CPU_STATIC plugin"


def collector_ram_usage_plugin():
    template_obj.start_subtemplate(subtemp_name="ALL NODES", op_level='collectors',plugin_name='ram_usage')
    print "succesfully started collector with RAM_USAGE plugin"

def collector_tcp_stats_plugin():
    template_obj.start_subtemplate(subtemp_name="ALL NODES", op_level='collectors',plugin_name='tcp_stats')
    print "succesfully started collector with TCP_STATS plugin"


def collector_disk_stats_plugin():
    template_obj.start_subtemplate(subtemp_name="ALL NODES", op_level='collectors',plugin_name='disk_stat')
    print "succesfully started collector with DISK_STATS plugin"

def collector_disk_usage_plugin():
    template_obj.start_subtemplate(subtemp_name="ALL NODES", op_level='collectors',plugin_name='disk_usage')
    print "succesfully started collector with DISK_USAGE plugin"

#collector_disk_usage_plugin()
#collector_disk_stats_plugin()
collector_tcp_stats_plugin()
#collector_ram_usage_plugin()
#collector_cpu_stats_plugin()
#collector_cpu_plugin()
#add_node_list()

