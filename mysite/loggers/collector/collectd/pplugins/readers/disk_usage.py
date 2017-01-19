#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Collectd python plugin to get overall system hard disk size and usage
'''

import subprocess
import sys
import re
import collectd
import exceptions

class DiskUsage:

    def __init__(self):
        self.interval = 10

    def config(self, cfg):
        for children in cfg.children:
            if children.key == 'interval':
                self.interval = children.values[0]

    def read(self):

                # Get the total size of storage media disk

        sd = \
            subprocess.Popen("lsblk -nbo KNAME,TYPE,SIZE | grep disk | grep sd | awk '{print $3}'",
                             shell=True, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        (lsblk, err) = sd.communicate()
        if err:
	    collectd.debug('disk_usage plugin: error in lsblk command')
            return
           

        sdlines = re.split('\n', lsblk)
        num_lines = len(sdlines)
        index = 0
        totalSum = 0
        while index < num_lines:
            line = sdlines[index]
            if line:
                totalSum = totalSum + int(line)
                index = index + 1
            else:
                index = index + 1

                # Find total usage using df -kl and grep all block devices from /dev

        sp = \
            subprocess.Popen("df -kl |awk '/^\/dev\//' | awk '{print $3}'",
                             shell=True, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        (df, err) = sp.communicate()
        if err:
            collectd.debug('disk_usage plugin: error in df command')
            return
            

        splines = re.split('\n', df)
        unum_lines = len(splines)
        uindex = 0
        usageSum = 0
        while uindex < unum_lines:
            line = splines[uindex]
            if line:
                usageSum = usageSum + int(line)  # usageSum is in Kb
                uindex = uindex + 1
            else:
                uindex = uindex + 1
                # print "Total".ljust(20)+"Usage".ljust(20)
                # print str(totalSum).ljust(20)+str(usageSum).ljust(20)
        ftotalSum = float(totalSum)/(1024 * 1024 * 1024)
        fusageSum = float((usageSum * 1024))/(1024 * 1024 * 1024)
        metric = collectd.Values()
        metric.plugin = 'disk_usage'
        metric.plugin_instance = 'Total'
        metric.interval = int(self.interval)
        metric.type = 'diskusage'
        metric.values = [ftotalSum, fusageSum]
        metric.dispatch()

    def read_temp(self):
        collectd.unregister_read(self.read_temp)
        collectd.register_read(self.read, interval=int(self.interval))


obj = DiskUsage()
collectd.register_config(obj.config)
collectd.register_read(obj.read_temp)
