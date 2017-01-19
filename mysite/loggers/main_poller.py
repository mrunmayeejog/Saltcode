from orchestrator import orch
import json
import os
import time
template_file = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), 'jobhandler','template', 'samples', 'sample_template_poller.json')

print "Reading Template:",template_file
template = None
with open(template_file) as data_file:
    template = json.load(data_file)

print template
template_obj= orch.Template()
print "Initialise template...."
template_id=template_obj.init_template(template=template)
#template_id=template_obj.init_template(template_id ='e3645c0e')
print "template_id : ", template_id

def poller_deploy():
    template_obj.deploy_template_poller()
    print "Successfully Poller deploy"

def poller_start():
    template_obj.start_template_poller()
    print "Successfully Poller Started"

def poller_teardown():
    template_obj.stop_template_poller()
    print "Successfully Poller Stopped"
    
def poller_update_plugin_meta():
    meta={"credentials":{"cluster_ip":"192.168.100.205","username":"mapr1","password":"mapr","port":8443}}
    template_obj.update_poller_plugin_meta(plugin_name='hadoop_cluster',meta=meta)
    template_obj.start_template_poller(sub_op='update')
    print "Successfully updated Poller Plugin meta"

def poller_plugin_target_add():
    target = "kafka-topic-test"
    template_obj.update_poller_plugin_target(plugin_name='hadoop_cluster', target=target, sub_op='add')
    template_obj.start_template_poller(sub_op='update')
    print "Successfully Added Poller Plugin target"
    
def poller_plugin_target_update():
    target = "kafka-topic-test"
    template_obj.update_poller_plugin_target(plugin_name='hadoop_cluster', target=target, sub_op='update')
    template_obj.start_template_poller(sub_op='update')
    print "Successfully updated Poller Plugin target"
    
def poller_plugin_target_delete():
    target = "kafka-topic-test"
    template_obj.update_poller_plugin_target(plugin_name='hadoop_cluster', target=target, sub_op='delete')
    template_obj.start_template_poller(sub_op='update')
    print "Successfully deleted Poller Plugin target"


poller_deploy()
time.sleep(30)
poller_start()
time.sleep(30)
#poller_plugin_target_add()
poller_plugin_target_delete()
time.sleep(50)
poller_teardown()
