import json
import qcomm

#user defined imports
from const import *


def dispatch_data(data, dest_q_list, tag=""):
    if tag:
        data[TAG] = tag
    for dest_q in dest_q_list:
        qcomm.put_msg(dest_q, data)


def extract_tag_interval_count(msg):
    tag = {}
    interval = DEFAULT_INTERVAL
    count = -1

    if TAG in msg.keys():
        tag = msg[TAG]
    if INTERVAL in msg.keys():
        interval = msg[INTERVAL]
    if RUN_COUNT in msg.keys():
        count = msg[RUN_COUNT]
    return tag, interval, count


def get_msgs(mgmt_q):
    data = {}
    if not qcomm.is_queue_empty(mgmt_q):
        data = qcomm.get_msg(mgmt_q)
    return data
