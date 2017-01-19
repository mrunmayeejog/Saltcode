#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Collectd python plugin to get disk stats [read count, write count, total read in bytes, total write in bytes]
'''

import subprocess
import re
import collectd
from libdiskstat import *


class DiskStat:

    def __init__(self):
        self.interval = 10

    def config(self, cfg):
        for children in cfg.children:
            if children.key == 'interval':
                self.interval = children.values[0]

    def dispatch_collectd(self, name, read_count, write_count, read_bytes, write_bytes):
        metric = collectd.Values()
        metric.plugin = 'disk_stat'
        metric.plugin_instance = name
        metric.interval = int(self.interval)
        metric.type = 'disk_diskstat'
        metric.values = [read_count, write_count, read_bytes, write_bytes]
        metric.dispatch()

    def read(self):
        sum_readc = 0
        sum_writec = 0
        sum_readbyte = 0
        sum_writebyte = 0
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

        #   print "NAME".ljust(20)+"Read IOPS  ".ljust(20)+"Write IOPS  ".ljust(20)+"Read tput in bytes ".ljust(20)+"Write tput in bytes  ".ljust(20)+"Read tput in mb  ".ljust(20)+"Write tput in mb   ".ljust(20)

        while index < num_lines:
            line = qdisk[index]
            if line:
                parts = re.split(r'\s+', line.strip())
                (name, type) = parts[:2]
                if type == 'disk':
                    io = diskio[name]
                    sum_readc = sum_readc + int(io.read_count)
                    sum_writec = sum_writec + int(io.write_count)
                    sum_readbyte = sum_readbyte + int(io.read_bytes)
                    sum_writebyte = sum_writebyte + int(io.write_bytes)
                    self.dispatch_collectd(name, io.read_count, io.write_count, io.read_bytes, io.write_bytes)

        #               print name.ljust(20)+str(io.read_count).ljust(20)+str(io.write_count).ljust(20)+str(io.read_bytes).ljust(20)+str(io.write_bytes).ljust(20)+str(io.read_mb).ljust(20)+str(io.write_mb).ljust(20)

                    index = index + 1
                else:
                    index = index + 1
            else:
                break

        #   print "Total".ljust(20)+str(sum_readc).ljust(20)+str(sum_writec).ljust(20)+str(sum_readbyte).ljust(20)+str(sum_writebyte).ljust(20)+str(sum_readmb).ljust(20)+str(sum_writemb).ljust(20)

        self.dispatch_collectd('Total', sum_readc, sum_writec, sum_readbyte, sum_writebyte)

    def read_temp(self):
        collectd.unregister_read(self.read_temp)
        collectd.register_read(self.read, interval=int(self.interval))


obj = DiskStat()
collectd.register_config(obj.config)
collectd.register_read(obj.read_temp)
