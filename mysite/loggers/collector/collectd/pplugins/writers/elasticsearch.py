import collectd
from requests.exceptions import ConnectionError
import requests
import json

class WriteElastic():
    def __init__(self):
        self.ip = "127.0.0.1"
        self.port = "9200"
        self.index = "test"
        self.ds_type = "test"
    
    def read_config(self, cfg):
        for children in cfg.children:
            if children.key=="ip":
                self.ip = children.values[0]
            elif children.key=="port":
                self.port = children.values[0]
            elif children.key=="index":
                self.index = children.values[0]
    def write_test(self, ds):
        data_dict = {}
        data_dict["plugin"] = ds.plugin
        data_dict["time"] = ds.time
        data_dict["values"] = ds.values
        try:
            data_dict["meta"] = ds.meta["tag"]
        except:
            data_dict["meta"] = ""
            pass
        url = "http://"+self.ip+":"+self.port+"/"+self.index+"/"+ds.plugin
        headers = {'content-type': 'application/json'}
        try:
            r = requests.post(url, data=json.dumps(data_dict), headers=headers, timeout=30)
        except Exception as e:
            r = "no response"
            ex_type, ex, tb = sys.exc_info()
            print '-->',traceback.print_tb(tb)
            print str(e)

obj = WriteElastic()
collectd.register_config(obj.read_config);
collectd.register_write(obj.write_test);

