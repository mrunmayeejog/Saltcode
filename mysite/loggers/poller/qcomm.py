import multiprocessing


def get_queue():
    return multiprocessing.Queue()


def is_queue_empty(queue):
    return queue.empty()


def get_msg(queue):
    return queue.get()


def put_msg(queue, data):
    return queue.put(data)
