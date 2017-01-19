import datetime
import imp
import json
from kafka import KafkaConsumer, KafkaProducer
import multiprocessing
import os
import sys
import time

#user defined modules
from const import *
import qcomm
import utils

#take kafka topics as arguments
if len(sys.argv) != 4:
    print("Provide - kafka_client, orch_comm and pcon_comm")
    exit(0)

kafka_client = sys.argv[1]
orch_comm = sys.argv[2]
pcon_comm = sys.argv[3]
'''
#kafka_client = '192.168.101.12:9092'
#orch_comm = 'orch_comm'
#pcon_comm = 'pcon_comm'
'''


def orch_consumer(orch_q, kafka_client, orch_comm):
    orch_comm_consumer = KafkaConsumer(orch_comm, bootstrap_servers=[kafka_client], value_deserializer=lambda m: json.loads(m.decode("ascii")))  # key_deserializer=lambda m: json.loads(m.decode("ascii")))
    for item in orch_comm_consumer:
        print item.value
        qcomm.put_msg(orch_q, item.value)
        orch_comm_consumer.commit()


def update_worker(cntrl_data, worker_proc_map, worker_target_map, worker_mgmt_queue_map, worker_metric_queue_map, worker_cntrl_list_map):
    worker_id = cntrl_data[PLUGIN_ID]

    if not worker_id in worker_proc_map.keys():
        print("Worker does not  exists -  what shall I update?")
        return False

    meta = dict(cntrl_data[META])
    #tag, interval, run_count = utils.extract_tag_interval_count(cntrl_data)
    #meta.update({TAG: tag})
    #meta.update({INTERVAL: interval})
    #meta.update({RUN_COUNT: run_count})

    qcomm.put_msg(worker_mgmt_queue_map[worker_id], cntrl_data)
    print("Update worker %s with - %s" % (worker_id, cntrl_data))

    index = 0
    for const in worker_cntrl_list_map:
        if const.keys()[0] == worker_id:
            worker_cntrl_list_map[index][worker_id][META] = meta
        index += 1

    return True


def get_writer_worker_inst(plugin, mgmt_q, state_q, metric_q, cntrl_data, state):
    meta = cntrl_data[META]
    while(True):
        update = utils.get_msgs(mgmt_q)
        if update:
            meta = update[META]

        doc = utils.get_msgs(metric_q)
        if doc:
            state = plugin.park(doc, meta, state)
            utils.dispatch_data(state, [state_q])


def get_reader_worker_inst(plugin, mgmt_q, state_q, dest_q_list, cntrl_data, state):
    tag = ""
    interval = ""
    run_count = -1

    meta = cntrl_data[META]
    tag, interval, run_count = utils.extract_tag_interval_count(cntrl_data)

    while(True):
        update = utils.get_msgs(mgmt_q)
        if update:
            meta = update[META]
            tag, interval, run_count = utils.extract_tag_interval_count(update)

        doc_list = []
        doc_list, state = plugin.poll(meta, state)

        for doc in doc_list:
            utils.dispatch_data(doc, dest_q_list, tag)

        utils.dispatch_data(state, [state_q])

        if run_count > 0:
            run_count = run_count - 1

        if run_count == 0:
            exit(0)

        time.sleep(interval)


def spin_worker(cntrl_data, worker_list, worker_proc_map, worker_target_map, worker_mgmt_queue_map, worker_queue_map, worker_metric_queue_map, worker_type_map, reader_to_tag_map, worker_to_mode_map, worker_state={}):
    plugin_id = cntrl_data[PLUGIN_ID]

    if plugin_id in worker_proc_map.keys():
        print("%s already exists -  why do you wanna restart?" % (worker_type_map[plugin_id]))
        return False

    uninitialized_writer_metric_q_map = {}

    plugin_type = cntrl_data[PLUGIN_TYPE]
    target = cntrl_data[TARGET]
    dest_list = []

    if plugin_type == READER:
        dest_list = cntrl_data[DEST_LIST]

    fpath = os.path.join(os.getcwd(), "poller/plugins", target) + ".py"
    plugin = imp.load_source(target, fpath)
    mgmt_q = qcomm.get_queue()
    state_q = qcomm.get_queue()
    meta = cntrl_data[META]

    if plugin_type == READER:
        target_writer = []
        for writer_id in dest_list:
            if writer_id not in worker_metric_queue_map.keys():
                print("Forming a metric queue in reader's call as target writer - %s still not activated" % (writer_id))
                metric_q = qcomm.get_queue()
                uninitialized_writer_metric_q_map[writer_id] = metric_q
            else:
                metric_q = worker_metric_queue_map[writer_id]
            target_writer.append(metric_q)
        #worker = multiprocessing.Process(target=(target), args=(mgmt_q, state_q, target_writer, meta, worker_state,))
        worker = multiprocessing.Process(target=get_reader_worker_inst, args=(plugin, mgmt_q, state_q, target_writer, cntrl_data, worker_state,))
    elif plugin_type == WRITER:
        if plugin_id not in worker_metric_queue_map.keys():
            metric_q = qcomm.get_queue()
        else:
            metric_q = worker_metric_queue_map[plugin_id]

        #worker = multiprocessing.Process(target=(target), args=(mgmt_q, state_q, metric_q, meta, worker_state,))
        worker = multiprocessing.Process(target=get_writer_worker_inst, args=(plugin, mgmt_q, state_q, metric_q, cntrl_data, worker_state,))
    else:
        print("spin_worker: Plugin type not recognized ", plugin_type)

    worker.start()

    worker_list.append(plugin_id)

    if plugin_type == READER:
        #reader_to_tag_map[plugin_id] = cntrl_data[META]["tag"]
        worker_target_map[plugin_id] = dest_list
        if uninitialized_writer_metric_q_map:
            worker_metric_queue_map.update(uninitialized_writer_metric_q_map)

    if plugin_type == WRITER:
        worker_metric_queue_map[plugin_id] = metric_q

    worker_mgmt_queue_map[plugin_id] = mgmt_q
    worker_queue_map[plugin_id] = state_q
    worker_proc_map[plugin_id] = worker
    #worker_target_map[plugin_id] = target
    worker_type_map[plugin_id] = plugin_type
    worker_to_mode_map[plugin_id] = cntrl_data["mode"]

    print("spin_worker - worker_proc_map:", worker_proc_map)
    print("spin_worker - worker_mgmt_queue_map:", worker_mgmt_queue_map)
    print("spin_worker - worker_queue_map:", worker_queue_map)
    print("spin_worker - worker_target_map:", worker_target_map)
    return True


def clear_worker_maps(worker_id, worker_proc_map, worker_target_map, worker_mgmt_queue_map,  worker_queue_map, worker_metric_queue_map, worker_type_map, worker_state_map, reader_to_tag_map):
    del worker_proc_map[worker_id]
    del worker_mgmt_queue_map[worker_id]
    del worker_queue_map[worker_id]
    del worker_state_map[worker_id]

    if worker_type_map[worker_id] == READER:
        del worker_target_map[worker_id]
        del reader_to_tag_map[worker_id]

    if worker_type_map[worker_id] == WRITER:
        del worker_metric_queue_map[worker_id]

    del worker_type_map[worker_id]


def stop_process(proc, worker_id):
    if proc.is_alive():
        proc.terminate()
        print("Terminated -", worker_id)
        #clear_worker_maps(worker_id, worker_proc_map, worker_target_map, worker_mgmt_queue_map,  worker_queue_map, worker_metric_queue_map, worker_type_map, worker_state_map, reader_to_tag_map)


def start_orch_comm(kafka_client, orch_comm):
    orch_q = qcomm.get_queue()
    orch_consumer_p = multiprocessing.Process(target=orch_consumer, args=(orch_q, kafka_client, orch_comm,))
    orch_consumer_p.start()
    print("Started orch_comm -- Yipee!!")
    return orch_consumer_p, orch_q


def controller(kafka_client, orch_comm, pcon_comm):
    beacon_interval = 10
    update_orch = True
    check_point = True
    time = datetime.datetime.now()
    worker_list = []
    #State recovery
    worker_cntrl_list_map = []
    #Mgmt queue for all workers
    worker_mgmt_queue_map = {}
    #Data queue for all workers
    worker_queue_map = {}
    #Write queues on which writers are waiting
    worker_metric_queue_map = {}
    #State update received from workers
    worker_state_map = {}
    #Worker to spwaned process map
    worker_proc_map = {}
    #Wroker to type reader or writer
    worker_type_map = {}
    #For readers what are the target writers
    worker_target_map = {}
    #Writer - Who are all writing to me? Not yet in use -- see if you need it -- I think you will.
    writer_to_reader_map = {}
    #Reader to tag map - Am I a writer or a reader? I dont know.
    reader_to_tag_map = {}
    #worker to level of intrusion map.
    worker_to_mode_map = {}
    #Worker run count
    worker_run_count = {}
    #Workers total run left - no cheat sheet!! (0 > infinite) (0 = kill the worker) (0 < keep count)
    #worker_lifes_left = {}

    #start orch_comm
    orch_consumer_p, orch_q = start_orch_comm(kafka_client, orch_comm)

    pcon_comm_producer = KafkaProducer(bootstrap_servers=kafka_client, value_serializer=lambda v: json.dumps(v).encode("utf-8"))

    while(True):
        #print ("Enter the realm of infinity")
        if not qcomm.is_queue_empty(orch_q):
            cntrl_data = json.loads(qcomm.get_msg(orch_q))
            #cntrl_data = qcomm.get_msg(orch_q)
            print ("Received contrl data %s" % cntrl_data)
            #Recovery -- you recover at the expanse of grace!!
            if cntrl_data[MSG_TYPE] == RECOVER:
                tmp_state_map = cntrl_data[CHECK_POINT][STATE]
                tmp_worker_cntrl_list_map = cntrl_data[CHECK_POINT][CNTRL_DATA_MAP]
                for const in tmp_worker_cntrl_list_map:
                    plugin_id = const.keys()[0]
                    cntrl_data = const[plugin_id]
                    if cntrl_data[PLUGIN_TYPE] == WRITER:
                        state = {}
                        spin_worker(cntrl_data, worker_list, worker_proc_map, worker_target_map, worker_mgmt_queue_map,  worker_queue_map, worker_metric_queue_map, worker_type_map, reader_to_tag_map, worker_to_mode_map, state)
                        worker_state_map[plugin_id] = state
                        worker_cntrl_list_map.append(const)
                for const in tmp_worker_cntrl_list_map:
                    plugin_id = const.keys()[0]
                    cntrl_data = const[plugin_id]
                    if cntrl_data[PLUGIN_TYPE] == READER:
                        state = tmp_state_map[plugin_id]
                        spin_worker(cntrl_data, worker_list, worker_proc_map, worker_target_map, worker_mgmt_queue_map,  worker_queue_map, worker_metric_queue_map, worker_type_map, reader_to_tag_map, worker_to_mode_map, state)
                        worker_state_map[plugin_id] = state
                        worker_cntrl_list_map.append(const)

            #asked to stop all readers and writers
            if cntrl_data[MSG_TYPE] == STOPALL:
                print "seriously teardown!!"
                for worker_id, proc in worker_proc_map.iteritems():
                    stop_process(proc, worker_id)

            #asked to bring down controller
            if cntrl_data[MSG_TYPE] == TEARDOWNALL:
                print "seriously teardown!!"
                for worker_id, proc in worker_proc_map.iteritems():
                    stop_process(proc, worker_id)
                stop_process(orch_consumer_p, "orch_comm")
                exit(0)

            #start/stop/manage each plugin - respect individuality
            if cntrl_data[MSG_TYPE] == CNTRL:
                print cntrl_data

                cmd = cntrl_data[CMD]

                if cmd == START:
                    worker_cntrl_list_map.append({cntrl_data[PLUGIN_ID]: cntrl_data})
                    spin_worker(cntrl_data, worker_list, worker_proc_map, worker_target_map, worker_mgmt_queue_map,  worker_queue_map, worker_metric_queue_map, worker_type_map, reader_to_tag_map, worker_to_mode_map)

                if cmd == STOP:
                    worker_id = cntrl_data[PLUGIN_ID]
                    stop_process(worker_proc_map[worker_id], worker_id)
                    #if worker_type_map[worker_id] == WRITER:
                    #    update_worker()

                if cmd == TEARDOWN:
                    worker_id = cntrl_data[PLUGIN_ID]
                    stop_process(worker_proc_map[worker_id], worker_id)
                    clear_worker_maps(worker_id, worker_proc_map, worker_target_map, worker_mgmt_queue_map,  worker_queue_map, worker_metric_queue_map, worker_type_map, worker_state_map, reader_to_tag_map)
                    #if worker_type_map[worker_id] == WRITER:
                    #    update_worker()

                if cmd == RESUME:
                    worker_id = cntrl_data[PLUGIN_ID]
                    restart_worker(worker_id, worker_proc_map, worker_mgmt_queue_map, worker_queue_map, worker_state_map, worker_cntrl_list_map, worker_metric_queue_map, worker_target_map, worker_type_map, worker_to_mode_map)

                if cmd == UPDATE:
                    worker_id = cntrl_data[PLUGIN_ID]
                    worker_type = worker_type_map[worker_id]

                    index = 0
                    for const in worker_cntrl_list_map:
                        if const.keys()[0] == worker_id:
                                worker_cntrl_list_map[index][worker_id][META] = cntrl_data[META]
                        index += 1

                    if worker_type == READER:
                        dest_list_new = cntrl_data[DEST_LIST]
                        dest_list = worker_target_map[worker_id]
                        if set(dest_list) != set(dest_list_new):
                            print "Have to restart for update - opps!!"
                            print("Update worker - %s, %s, %s, %s" % (worker_id, worker_type, dest_list_new, dest_list))
                            index = 0
                            for const in worker_cntrl_list_map:
                                if const.keys()[0] == worker_id:
                                    worker_cntrl_list_map[index][worker_id][DEST_LIST] = dest_list_new
                                index += 1

                            worker_proc_map[worker_id].terminate()
                            restart_worker(worker_id, worker_proc_map, worker_mgmt_queue_map, worker_queue_map, worker_state_map, worker_cntrl_list_map, worker_metric_queue_map, worker_target_map, worker_type_map, worker_to_mode_map)
                        else:
                            print("Update worker - %s, %s" % (worker_id, worker_type))
                            update_worker(cntrl_data, worker_proc_map, worker_target_map, worker_mgmt_queue_map, worker_metric_queue_map, worker_cntrl_list_map)
                    else:
                        print("Update worker - %s, %s" % (worker_id, worker_type))
                        update_worker(cntrl_data, worker_proc_map, worker_target_map, worker_mgmt_queue_map, worker_metric_queue_map, worker_cntrl_list_map)

        for worker_id, worker_q in worker_queue_map.iteritems():
            if not qcomm.is_queue_empty(worker_q):
                #update state info
                state = qcomm.get_msg(worker_q)
                worker_state_map[worker_id] = state
                #print("worker state -", worker_state_map)

        #beacon -- should it be threaded?
        time_delta_sec = (datetime.datetime.now() - time).total_seconds()
        if time_delta_sec >= beacon_interval:
            #Do checkpointing
            if check_point:
                data = {CHECK_POINT: {CNTRL_DATA_MAP: worker_cntrl_list_map, STATE: worker_state_map}}
                pcon_comm_producer.send(pcon_comm, json.dumps(data))
                print("checkpoint using-")
                print data
            print("Its time for revival!! - so much time has elapsed %s" %
                  (time_delta_sec))
            #check orch_comm
            if not orch_consumer_p.is_alive():
                orch_consumer_p, orch_q = start_orch_comm(kafka_client,
                                                          orch_comm)

            #worry about workers now
            tmp_worker_proc_map = dict(worker_proc_map)
            for worker_id, proc in tmp_worker_proc_map.iteritems():
                if not proc.is_alive():
                    print("Found %s is quite dead" % (worker_id))
                    if worker_to_mode_map[worker_id] == "manage":
                        restart_worker(worker_id,
                                       worker_proc_map,
                                       worker_mgmt_queue_map,
                                       worker_queue_map,
                                       worker_state_map,
                                       worker_cntrl_list_map,
                                       worker_metric_queue_map,
                                       worker_target_map,
                                       worker_type_map,
                                       worker_to_mode_map)
            time = datetime.datetime.now()


def restart_worker(worker_id,
                   worker_proc_map,
                   worker_mgmt_queue_map,
                   worker_queue_map,
                   worker_state_map,
                   worker_cntrl_list_map,
                   worker_metric_queue_map,
                   worker_target_map,
                   worker_type_map,
                   worker_to_mode_map):
        mgmt_q = worker_mgmt_queue_map[worker_id]
        state_q = worker_queue_map[worker_id]
        target_writer = []
        state = {}
        plugin_type = worker_type_map[worker_id]

        for const in worker_cntrl_list_map:
            if worker_id == const.keys()[0]:
                cntrl_data = const[worker_id]
        meta = cntrl_data[META]

        target = cntrl_data[TARGET]
        fpath = os.path.join(os.getcwd(), "poller/plugins", target) + ".py"
        plugin = imp.load_source(target, fpath)
        #target = eval("%s.%s" % ("plugin",target))

        try:
            worker_state = worker_state_map[worker_id]
        except:
            worker_state = {}

        if plugin_type == READER:
            dest_list = cntrl_data[DEST_LIST]
            for writer_id in dest_list:
                target_writer.append(worker_metric_queue_map[writer_id])
            print("Going to restart worker %s, %s, %s, %s" %
                  (worker_id, plugin_type, dest_list, target_writer))
            worker = multiprocessing.Process(target=get_reader_worker_inst, args=(plugin, mgmt_q, state_q, target_writer, cntrl_data, worker_state,))
        elif plugin_type == WRITER:
            metric_q = worker_metric_queue_map[worker_id]
            worker = multiprocessing.Process(target=get_writer_worker_inst,
                                             args=(plugin, mgmt_q, state_q,
                                             metric_q, cntrl_data,
                                             worker_state,))
            print("Going to restart worker %s, %s, %s" %
                  (worker_id, plugin_type, metric_q))
        worker.start()
        worker_proc_map[worker_id] = worker

        if plugin_type == READER:
            worker_target_map[worker_id] = dest_list

#Start controller
#controller('192.168.101.12:9092', 'orch_comm', 'pcon_comm')
controller(kafka_client, orch_comm, pcon_comm)
