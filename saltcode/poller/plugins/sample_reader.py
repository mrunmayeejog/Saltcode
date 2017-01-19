import os

def poll(meta={}, state={}):
    #use meta and state as you would prefer
    return [{"poll":str(os.getpid())}], state
