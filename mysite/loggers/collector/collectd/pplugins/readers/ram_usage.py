'''
Python Script to get RAM usage
'''

import subprocess
import re
import signal
import collectd


class ram:
    def __init__(self):
        self.interval = 8

    def read_config(self, cfg):
        for children in cfg.children:
            if children.key == 'interval':
                self.interval = children.values[0]

    def ram_usage(self):
        """
            Procedure to get Total RAM size and used Percentage
        """
        sd = subprocess.Popen("free -m",shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (ramusage, err) = sd.communicate()
        if err:
            collectd.debug("ram_usage plugin: %s" %err)
            return
        ramusage = ramusage.split("\n")
        total_and_used = r'\S+\s+(\d+)\s+(\d+)\s+\d+\s+\d+\s+\d+\s+\d+'
        for i in range(0, len(ramusage)):
            if 'Mem' in ramusage[i]:
                usage_result = re.search(total_and_used, ramusage[i])
                if usage_result:
                    total = float(usage_result.group(1))/1024
                    used = float(usage_result.group(2))/1024
                    usedper = (float(used)/float(total))*100
                    metric = collectd.Values()
                    metric.plugin = 'ram_usage'
                    metric.type = 'ramusage'
                    metric.values = [total, usedper]
                    metric.interval = int(self.interval)
                    metric.dispatch()
                    collectd.debug("ram_usage plugin: Values are dispatched successfully")
                    break

    def init(self):
        signal.signal(signal.SIGCHLD, signal.SIG_DFL)

    def read_temp(self):
        collectd.unregister_read(self.read_temp)
        collectd.register_read(self.ram_usage, interval=int(self.interval))

raminstance = ram()
collectd.register_init(raminstance.init)
collectd.register_config(raminstance.read_config)
collectd.register_read(raminstance.read_temp)
