import json
import requests


def park(doc, meta={}, state={}):
    if not state:
        state["No_Client"] = 0
        state["No_Topic"] = 0
        state["No_DS_Type"] = 0
        state["Send_Success"] = 0
        state["Send_Failed"] = 0

    try:
        client = ("%s:%s" % (meta["host"], meta["port"]))
    except:
        state["No_Client"] = state["No_Client"] + 1
        return state

    try:
        index = meta["index"]
    except:
        state["No_Index"] = state["No_Index"] + 1
        return state

    try:
        ds_type = meta["ds_type"]
    except:
        state["No_DS_Type"] = state["No_DS_Type"] + 1
        return state

    url = "http://%s/%s/%s" % (client, index, ds_type)
    headers = {'content-type': 'application/json'}

    try:
        resp = requests.post(url, data=json.dumps(doc),
                             headers=headers, timeout=30)
        state["Send_Success"] = state["Send_Success"] + 1
    except:
        state["Send_Failed"] = state["Send_Failed"] + 1
    return state
