import re
import commands
import collectd
import signal

nic_tx_rx = '(\w+)+\:+\s+(\d+)\s+(\d+)\s+\d+\s+(\d+)\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)\s+(\d+)\s+\d+\s+(\d+)+\s+\d+\s+\d+\s+\d+\s+\d'
mac_ip_name = {'mac_address': r'link/ether+\s+(\S+)\s+\w+\s+\S+', 'ip_address': r'inet+\s+(\S+)+\s+\w+\s+\S+\s+\w+\s+\w+\s+\w+'}


class nicstats:
    def __init__(self):
        self.interval = 10

    def read_config(self, cfg):
        for children in cfg.children:
            if children.key == 'interval':
                self.interval = children.values[0]

    def init(self):
        signal.signal(signal.SIGCHLD, signal.SIG_DFL)

    def get_status_up_down(self, nicname):
        up_down = commands.getoutput('ip link show dev %s' % nicname)
        up_down = up_down.split(' ')
        if up_down[8] == 'UP':
            return 1
        return 0

    def parse(self, mac_ip_output):
        for key, val in mac_ip_name.items():
            mac_ip = {}
            mac_or_ip = re.search(val, mac_ip_output)

            if 'secondary' in mac_ip_output:
                virtual = mac_ip_output.split(" ")
                mac_ip['ip_address'] = virtual[5]
                mac_ip['name'] = virtual[11]
                mac_ip['mtu'] = 0
                mac_ip['mac_address'] = 0
                mac_ip['up_down'] = self.get_status_up_down(mac_ip['name'])
                return "ip_address", mac_ip

            if 'mtu' in mac_ip_output:
                name_mtu = mac_ip_output.split(" ")
                mac_ip['name'] = str(name_mtu[1]).strip(":")
                mac_ip['mtu'] = name_mtu[4]
                mac_ip['up_down'] = self.get_status_up_down(mac_ip['name'])
                return 'name', mac_ip

            if mac_or_ip:
                mac_ip[key] = mac_or_ip.group(1)
                return key, mac_ip
        return -1, -1

    def get_mac_ip_address(self):
        mac_ip_output = commands.getoutput('ip a')
        line = str(mac_ip_output).split("\n")
        mac_mtu = {}
        for i in range(0, len(line)):
            key, mac_ip = self.parse(line[i])
            if key == -1:
                continue
            if key == 'name':
                mac_mtu[mac_ip['name']] = {}
                namekey = mac_ip['name']
                mac_mtu[mac_ip['name']]['mtu'] = mac_ip['mtu']
                mac_mtu[mac_ip['name']]['ip_address'] = 0
                mac_mtu[mac_ip['name']]['mac_address'] = 0
                mac_mtu[mac_ip['name']]['up_down'] = mac_ip['up_down']
            elif 'secondary' in line[i]:
                mac_mtu[mac_ip['name']] = {}
                mac_mtu[mac_ip['name']]['ip_address'] = mac_ip['ip_address']
                mac_mtu[mac_ip['name']]['mac_address'] = mac_ip['mac_address']
                mac_mtu[mac_ip['name']]['mtu'] = 0
                mac_mtu[mac_ip['name']]['up_down'] = mac_ip['up_down']
            elif mac_ip:
                mac_mtu[namekey][key] = mac_ip[key]
        return mac_mtu

    def getnicspeed(self, nicname):
        nic_speed = commands.getoutput("ethtool %s" % nicname)
        nic_speed = nic_speed.split("\n")
        for line in nic_speed:
            if 'Speed' not in line:
                continue
            else:
                speed = line.split(":")
                return speed[1]

    def collectd_plugin(self, nicname, nic, values=None):
        metric = collectd.Values()
        if values is None:
            metric.plugin = "nic_stats"
            metric.plugin_instance = nicname
            metric.type = "nicstats"
            metric.meta["name"] = nic["name"]
            metric.meta["ip_address"] = nic["ip_address"]
            metric.meta["mac_address"] = nic["mac_address"]
            metric.meta["speed"] = nic["speed"]
            metric.values = [nic['mtu'], nic['rx_data_counter'], nic['tx_data_counter'], nic['rx_drop_counter'], nic['tx_drop_counter'], nic['read'], nic['write']]
        else:
            metric.plugin = "nic_stats"
            metric.type = "nicstataggregate"
            metric.plugin_instance = "total"
            metric.values = values
        metric.interval = int(self.interval)
        metric.dispatch()

    def nic_status(self):
        f = open('/proc/net/dev', 'r')
        if f is None:
            return (-1)
        nic_tx_rx_data = f.read()
        f.close()
        if nic_tx_rx_data is None:
            return (-1)
        nic = {}
        mac_mtu = self.get_mac_ip_address()
        aggr_rx_counter = 0
        aggr_tx_counter = 0
        aggr_read_rate = 0
        aggr_write_rate = 0
        aggr_tx_drop = 0
        aggr_rx_drop = 0
        aggr_mtu = 0
        physical = []
        for item in nic_tx_rx_data.split("\n"):
            nic_stats = re.search(nic_tx_rx, item)
            if nic_stats:
                if nic_stats.group(1) == 'lo':
                    continue
                nic['name'] = nic_stats.group(1)
                physical.append(nic_stats.group(1))
                nic['read'] = nic_stats.group(2)
                nic['rx_data_counter'] = nic_stats.group(3)
                nic['rx_drop_counter'] = nic_stats.group(4)
                nic['write'] = nic_stats.group(5)
                nic['tx_data_counter'] = nic_stats.group(6)
                nic['tx_drop_counter'] = nic_stats.group(7)
                nic['mtu'] = mac_mtu[nic['name']]['mtu']
                nic['ip_address'] = mac_mtu[nic['name']]['ip_address']
                nic['mac_address'] = mac_mtu[nic['name']]['mac_address']
                nic['up_down'] = mac_mtu[nic['name']]['up_down']
                nic['speed'] = self.getnicspeed(nic['name'])
                nic['interface_type'] = 1
                aggr_rx_counter = aggr_rx_counter + int(nic['rx_data_counter'])
                aggr_tx_counter = aggr_tx_counter + int(nic['tx_data_counter'])
                aggr_read_rate = aggr_read_rate + int(nic['read'])
                aggr_write_rate = aggr_read_rate + int(nic['write'])
                aggr_rx_drop = aggr_rx_drop + int(nic['rx_drop_counter'])
                aggr_tx_drop = aggr_tx_drop + int(nic['tx_drop_counter'])
                self.collectd_plugin(nic['name'], nic)

        for key, val in mac_mtu.items():
            if key == 'lo':
                continue
            for inter in physical:
                flag = 0
                if inter == key:
                    flag = 1
                    break
            if flag == 0:
                nic['name'] = key
                nic['ip_address'] = mac_mtu[nic['name']]['ip_address']
                nic['mac_address'] = mac_mtu[nic['name']]['mac_address']
                nic['up_down'] = mac_mtu[nic['name']]['up_down']
                nic['interface_type'] = 0
                nic['mtu'] = mac_mtu[nic['name']]['mtu']
                nic['rx_drop_counter'] = nic['rx_data_counter'] = nic['tx_drop_counter'] = nic['tx_data_counter'] = nic['write'] = nic['read'] = 0
                self.collectd_plugin(nic['name'], nic)
        self.collectd_plugin(None, None, [aggr_rx_counter, aggr_tx_counter, aggr_rx_drop, aggr_tx_drop, aggr_read_rate, aggr_write_rate])

    def read_temp(self):
        collectd.unregister_read(self.read_temp)
        collectd.register_read(self.nic_status, interval=int(self.interval))

nicinstance = nicstats()
collectd.register_init(nicinstance.init)
collectd.register_config(nicinstance.read_config)
collectd.register_read(nicinstance.read_temp)
