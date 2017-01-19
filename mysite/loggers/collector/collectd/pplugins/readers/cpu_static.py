from __future__ import division
import collectd
import re


class CpuStatic():

    def __init__(self):
        self.interval = 14

    def read_config(self, cfg):
        for children in cfg.children:
            if children.key == 'interval':
                self.interval = children.values[0]

    def read(self):
        total_logical_cpus = 0
        total_physical_cpus = 0
        total_cores = 0
        keyword_processor_found = False
        keyword_physical_id_found = False
        keyword_core_id_found = False
        logical_cpus = {}
        physical_cpus = {}
        cores = {}
        hyperthreading = 0
        model_list = []
        total_freq = 0
        count_freq = 0

        f = open('/proc/cpuinfo', 'r')
        if f is None:
            ERROR("cpustatic plugin: Unable to open /proc/cpuinfo")
            return(-1)
        lines = f.readlines()
        index = 0
        while index < len(lines):
            line = lines[index]
            if re.match('processor', line):
                cpu = int(line.split()[2])
                keyword_processor_found = True

                if not (cpu in logical_cpus):
                    logical_cpus[cpu] = []
                    total_logical_cpus += 1

            if re.match('physical id', line):
                phys_id = int(line.split()[3])
                keyword_physical_id_found = True

                if not (phys_id in physical_cpus):
                    physical_cpus[phys_id] = []
                    total_physical_cpus += 1

            if re.match('core id', line):
                core = int(line.split()[3])
                keyword_core_id_found = True

                if not (core in cores):
                    cores[core] = []
                    total_cores += 1

            if re.match('model name', line):
                modelname = line.split(":")
                modelname = str(modelname[1]).strip(' ')
                modelname = modelname.strip('\n')
                if modelname not in model_list:
                    model_list.append(modelname)

            if re.match("cpu MHz", line):
                total_freq = total_freq + float(line.split()[3])
                count_freq = count_freq + 1

            index = index+1

        if keyword_processor_found and keyword_physical_id_found and keyword_core_id_found:
            if (total_cores * total_physical_cpus) * 2 == total_logical_cpus:
                hyperthreading = 1
            model_name = ",".join(model_list)

        metric = collectd.Values()
        metric.plugin = 'cpu_static'
        metric.meta["modulename"] = modelname
        metric.meta["average_freq"] = total_freq/count_freq
        metric.type = 'cpustats'
        metric.values = [total_physical_cpus, total_cores, total_logical_cpus, hyperthreading]
        metric.interval = int(self.interval)
        metric.dispatch()

    def read_temp(self):
        collectd.unregister_read(self.read_temp)
        collectd.register_read(self.read, interval=int(self.interval))

cpu_instance = CpuStatic()
collectd.register_config(cpu_instance.read_config)
collectd.register_read(cpu_instance.read_temp)
