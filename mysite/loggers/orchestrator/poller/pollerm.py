import json
from kafka import KafkaConsumer, KafkaProducer
import multiprocessing
import os

# user defined modules
from const import *
import settings


class PollerManager:

    controller_id = -1
    template = {}
    orch_comm = ""
    pcon_comm = ""
    orch_comm_producer = None
    pcon_comm_consumer = None
    kafka_client = ""
    controller_p = None
    check_point = {}
    plugin_id_map = {}
    plugin_count_map = {}

    def __init__(self, template={}):
        self.pcontroller = settings.CONTROLLER
        self.controller_id = 0
        self.template = template
        self.orch_comm = settings.ORCH_COMM
        self.pcon_comm = settings.PCON_COMM
        self.kafka_client = settings.KAFKA_CLIENT
        self.controller_p = None

    def deploy(self):
        # Provision poller
        self.orch_comm_producer = KafkaProducer(bootstrap_servers=self.kafka_client, value_serializer=lambda v: json.dumps(v).encode("utf-8"))
        self.pcon_comm_consumer = KafkaConsumer(self.pcon_comm, bootstrap_servers=[self.kafka_client], value_deserializer=lambda m: json.loads(m.decode("ascii")))
        controller = 'python' + ' ' + self.pcontroller + ' ' + self.kafka_client + ' ' + self.orch_comm + ' ' + self.pcon_comm + ' &'
        print controller
        os.system(controller)

    def start(self, template, dirty_list):
        # start poller
        targets = template[POLLER][TARGETS]
        for item in targets:
            if ((not dirty_list) or (item[NAME] in dirty_list)):
                msg = self.build_msg(item, inst_type=TARGET, op=START)
                self.send_to_controller(msg)
                print msg
        for item in template[POLLER][PLUGINS]:
            if ((not dirty_list) or (item[NAME] in dirty_list)):
                msg = self.build_msg(item, inst_type=PLUGIN, op=START)
                self.send_to_controller(msg)
                print msg

    def resume(self, template, dirty_list):
        # resume poller
        targets = template[POLLER][TARGETS]
        for item in targets:
            if ((not dirty_list) or (item[NAME] in dirty_list)):
                msg = self.build_msg(item, inst_type=TARGET, op=RESUME)
                self.send_to_controller(msg)
                print msg
        for item in template[POLLER][PLUGINS]:
            if ((not dirty_list) or (item[NAME] in dirty_list)):
                msg = self.build_msg(item, inst_type=PLUGIN, op=RESUME)
                self.send_to_controller(msg)
                print msg

    def update(self, template, dirty_list):
        # start poller
        targets = template[POLLER][TARGETS]
        for item in targets:
            if ((not dirty_list) or (item[NAME] in dirty_list)):
                msg = self.build_msg(item, inst_type=TARGET, op=UPDATE)
                self.send_to_controller(msg)
        for item in template[POLLER][PLUGINS]:
            if ((not dirty_list) or (item[NAME] in dirty_list)):
                msg = self.build_msg(item, inst_type=PLUGIN, op=UPDATE)
                self.send_to_controller(msg)

    def stop(self, template, dirty_list):
        # stop poller plugin
        targets = template[POLLER][TARGETS]
        for item in targets:
            if ((not dirty_list) or (item[NAME] in dirty_list)):
                msg = self.build_msg(item, inst_type=TARGET, op=STOP)
                self.send_to_controller(msg)
        for item in template[POLLER][PLUGINS]:
            if ((not dirty_list) or (item[NAME] in dirty_list)):
                msg = self.build_msg(item, inst_type=PLUGIN, op=STOP)
                self.send_to_controller(msg)

    def teardownall(self, template):
        # teardown poller
        msg = {}
        msg = self.build_msg(msg, op=TEARDOWNALL)
        if msg:
            self.send_to_controller(msg)
        else:
            print ("Failed to teardown")

    def teardown(self, template):
        # teardown poller
        msg = {}
        msg = self.build_msg(msg, op=TEARDOWN)
        if msg:
            self.send_to_controller(msg)
        else:
            print ("Failed to teardown")

    def teardown_inst(self):
        # teardown poller
        pass

    def check_status(self, plugin_id=""):
        # get status of poller or plugin
        status = {}
        partitions = self.pcon_comm_consumer.poll(100000)
        if len(partitions) > 0:
            for p in partitions:
                if not plugin_id:
                    try:
                        status = json.loads((partitions[p][-1].value))[CHECK_POINT][STATE]
                        return status
                    except:
                        pass
                else:
                    try:
                        status = json.loads((partitions[p][-1].value))[CHECK_POINT][STATE][plugin_id]
                        return status
                    except:
                        pass
        return status

    def build_msg(self, msg, inst_type=PLUGIN, op=START):
        if op == TEARDOWNALL:
            msg = {MSG_TYPE: TEARDOWNALL}
        if op == STOPALL:
            msg = {MSG_TYPE: STOPALL}
        if op == START or op == UPDATE or op == STOP or op == RESUME or op == TEARDOWN:
            msg.update({MSG_TYPE: CNTRL})
            msg.update({CMD: op})
            msg.update({PLUGIN_ID: msg[NAME]})
            if inst_type == PLUGIN:
                msg.update({PLUGIN_TYPE: READER})
                msg.update({DEST_LIST: msg[TARGETS]})
            if inst_type == TARGET:
                msg.update({PLUGIN_TYPE: WRITER})
        msg["id"] = self.controller_id
        return msg

    def send_to_controller(self, msg):
        try:
            self.orch_comm_producer.send(self.orch_comm, json.dumps(msg))
            self.orch_comm_producer.flush()
        except:
            print ("Failed to send to - orch_comm")

    def generate_id(self, plugin_name):
        return plugin_name + "_" + str(self.plugin_count_map[plugin_name]) + "_" + str(self.controller_id)
