#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Collectd python plugin to get disk performance [disk name, read iops, write iops, read throughput, write throughput, read counter, write counter]
'''

import subprocess
import re
from libdiskio import *
import collectd


class DiskIostat:

    def __init__(self):
        self.interval = 10

    def config(self, cfg):
        for children in cfg.children:
            if children.key == 'interval':
                self.interval = children.values[0]

    def dispatch_collectd(self, name, read_iops, write_iops, read_tput, write_tput, read_c, write_c):
        metric = collectd.Values()
        metric.plugin = 'disk_iostat'
        metric.plugin_instance = name
        metric.interval = int(self.interval)
        metric.type = 'disk_iostat'
        metric.values = [float(read_iops), float(write_iops), float(read_tput), float(write_tput), read_c, write_c]
        metric.dispatch()

    def read(self):
        sum_readiops = 0.00
        sum_writeiops = 0.00
        sum_readbyte = 0
        sum_writebyte = 0
        sum_readthrput = 0.00
        sum_writethrput = 0.00
        q = subprocess.Popen('lsblk -no KNAME,TYPE | grep disk',
                             shell=True, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        (lsblk, err) = q.communicate()
        if err:
            print 'err in lsblk command'
            sys.exit(0)
        qdisk = re.split('\n', lsblk)
        index = 0
        num_lines = len(qdisk)
        diskio = disk_io_counters()
        iostat = io_stat()

        #   print "NAME".ljust(20)+"Read IOPS  ".ljust(20)+"Write IOPS  ".ljust(20)+"Read tput in mb ".ljust(20)+"Write tput in mb  ".ljust(20)+"Read data counter  ".ljust(20)+"Write data counter ".ljust(20)

        while index < num_lines:
            line = qdisk[index]
            if line:
                parts = re.split(r'\s+', line.strip())
                (name, type) = parts[:2]
                if type == 'disk':
                    io = diskio[name]
                    if name in iostat:
                        stat = iostat[name]
                        sum_readiops = sum_readiops \
                            + float(stat.read_iops)
                        sum_writeiops = sum_writeiops \
                            + float(stat.write_iops)
                        sum_readthrput = sum_readthrput \
                            + float(stat.read_thrput)
                        sum_writethrput = sum_writethrput \
                            + float(stat.write_thrput)
                        sum_readbyte = sum_readbyte + int(io.read_bytes)
                        sum_writebyte = sum_writebyte \
                            + int(io.write_bytes)

        #                       print name.ljust(20)+str(stat.read_iops).ljust(20)+str(stat.write_iops).ljust(20)+str(stat.read_thrput).ljust(20)+str(stat.write_thrput).ljust(20)+str(io.read_bytes).ljust(20)+str(io.write_bytes).ljust(20)

                        self.dispatch_collectd(name, stat.read_iops, stat.write_iops, stat.read_thrput, stat.write_thrput, io.read_bytes, io.write_bytes)
                    else:

                                # disk which are not displayed by iostat. eg:fd0

                        sum_readiops = sum_readiops + 0.00
                        sum_writeiops = sum_writeiops + 0.00
                        sum_readthrput = sum_readthrput + 0.00
                        sum_writethrput = sum_writethrput + 0.00
                        sum_readbyte = sum_readbyte + int(io.read_bytes)
                        sum_writebyte = sum_writebyte + int(io.write_bytes)

        #                       print name.ljust(20)+str(0.0).ljust(20)+str(0.0).ljust(20)+str(0.0).ljust(20)+str(0.0).ljust(20)+str(io.read_bytes).ljust(20)+str(io.write_bytes).ljust(20)

                        self.dispatch_collectd(name, 0.00, 0.00, 0.00, 0.00, io.read_bytes, io.write_bytes)
                    index = index + 1
                else:
                    index = index + 1
            else:
                break

        #   print "Total".ljust(20)+str(sum_readiops).ljust(20)+str(sum_writeiops).ljust(20)+str(sum_readthrput).ljust(20)+str(sum_writethrput).ljust(20)+str(sum_readbyte).ljust(20)+str(sum_writebyte).ljust(20)

        self.dispatch_collectd('Total', sum_readiops, sum_writeiops, sum_readthrput, sum_writethrput, sum_readbyte, sum_writebyte)

    def read_temp(self):
        collectd.unregister_read(self.read_temp)
        collectd.register_read(self.read, interval=int(self.interval))


obj = DiskIostat()
collectd.register_config(obj.config)
collectd.register_read(obj.read_temp)
