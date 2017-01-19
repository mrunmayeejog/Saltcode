'''
Python Script to  get TCP/IP buffer size S1/S2/S3(Low,Medium and High)
'''

import subprocess
import collectd
import signal
import re


class tcp_stats:

    def __init__(self):
        self.interval = 8

    def read_config(self, cfg):
        for children in cfg.children:
            if children.key == 'interval':
                self.interval = children.values[0]

    def get_retra_reset(self):
        """
            Procedure to get tcp_reset and tcp_retrans values.
        """
        retrans = resets_recv = resets_sent = 0
        sd = subprocess.Popen("cat /proc/net/snmp",shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (snmp_output, err) = sd.communicate()
        if err:
            collectd.debug('tcp_stats plugin:%s' %err)
            return
        snmp_output = snmp_output.split("\n")
        flag = 0
        for i in range(0, len(snmp_output)):
            if 'Tcp:' not in snmp_output[i]:
                continue
            if flag:
                tcp_stat = snmp_output[i].split(" ")
                resets_recv = tcp_stat[8]
                retrans = tcp_stat[12]
                resets_sent = tcp_stat[14]
                return retrans, resets_sent, resets_recv
            flag = flag + 1

    def get_buffer_size(self):
        """
            Procedure to get read and write buffer size(low, medium and high) and also to dispatch values to collectd plugin.
        """
        read_write_buffer = r'(\d+)+\s+(\d+)\s+(\d+)'
        command = ['cat /proc/sys/net/ipv4/tcp_wmem', 'cat /proc/sys/net/ipv4/tcp_rmem']
        read_min = read_medium = read_max = write_min = write_medium = write_max = 0
        retrans = resets_recv = resets_sent = 0
        for commd in command:
            sd = subprocess.Popen("%s"%commd,shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            (buffersize, err) = sd.communicate()
            if err:
                collectd.debug('tcp_stats plugin: %s' %err)
                return 
            buffersize = re.search(read_write_buffer, buffersize)
            if buffersize:
                if 'w' in commd:
                    read_min = float(buffersize.group(1))/1024
                    read_medium = float(buffersize.group(2))/1024
                    read_max = float(buffersize.group(3))/1024
                    collectd.debug("TCP write buffer size got successfully")
                elif 'r' in commd:
                    write_min = float(buffersize.group(1))/1024
                    write_medium = float(buffersize.group(2))/1024
                    write_max = float(buffersize.group(3))/1024
                    collectd.debug("TCP read buffer size got successfully")
        try:
            retrans, resets_sent, resets_recv = self.get_retra_reset()
            collectd.debug("TCP reset and retransmitt values got successfully")
        except:
            return
        metric = collectd.Values()
        metric.plugin = "tcp_stats"
        metric.type = "tcpstats"
        metric.values = [read_min, write_min, read_medium, write_medium, read_max, write_max, retrans, resets_sent, resets_recv]
        metric.interval = int(self.interval)
        metric.dispatch()

    def init(self):
        signal.signal(signal.SIGCHLD, signal.SIG_DFL)

    def read_temp(self):
        collectd.unregister_read(self.read_temp)
        collectd.register_read(self.get_buffer_size, interval=int(self.interval))


tcp_instance = tcp_stats()
collectd.register_init(tcp_instance.init)
collectd.register_config(tcp_instance.read_config)
collectd.register_read(tcp_instance.read_temp)
