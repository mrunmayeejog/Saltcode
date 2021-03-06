'''
Mapr Hadoop Cluster Poller to poll cluster level details

Prerequisites: Install python package using following command
                   pip install requests==2.12.3
Parameter:
            {
            'cluster_ip': <mapr-cluster-ip>,
            'username': <mapr-user>,
            'password': <mapr-passwors>,
            'port': <mapr-cluster-port>, # Port where cluster webserver running
            }

'''

import requests
import json
import time
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import abc

__author__ = 'Anand Nevase'

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

service_status = {
    0: 'Not configured',
    1: 'Configured',
    2: 'Running',
    3: 'Stopped',
    4: 'Failed',
    5: 'Stand by'
}


class HadoopClusterPoller():

    _NAME_ = "Hadoop Cluster Poller"

    def __init__(self, config):
        self.config = config
        self.configure()
        self.result = []

    def load_config(config):
        self.config = config
        self.configure()

    def get_name(self):
        return HadoopClusterPoller._NAME_

    def configure(self):
        self.cluster_host = self.config.get('cluster_ip')
        self.username = self.config.get('username')
        self.password = self.config.get('password')
        self.port = self.config.get('port')

    def __update_result(self, result={}):
        self.result.append(result)

    def __call_rest_api(self, rest_call):
        connection_url = "https://{}:{}{}".format(
            self.cluster_host, self.port, rest_call)
        response = requests.get(connection_url, auth=(
            self.username, self.password), verify=False)
        return json.loads(response.text).get('data')

    def poll(self):
        try:
            dashboard_info_rest_url = '/rest/dashboard/info'
            cluster_list = self.__call_rest_api(dashboard_info_rest_url)
            cluster_info = dict(cluster_list[0])
            self.cluster_id = cluster_info.get('cluster').get('id')
            self.__cldbs_status()
            self.__zookeeper_status()
            self.__yarn_details()
            self.__nodes_status()
            self.__node_services_status()
            success_status = {
                "status": "COMPLETED",
                "status_message": "Hadoop Cluster poll completed successfully"
            }
            return self.result, dict(success_status)

        except Exception as e:
            exception_status = {
                "status": "EXCEPTION",
                "status_message": str(e)
            }
            return self.result, exception_status
#

    def __nodes_status(self):
        node_list_rest_url = '/rest/node/list?columns=health,healthDesc,id,ip,hostname'
        node_list_result = self.__call_rest_api(node_list_rest_url)
        self.__update_result(
            {'cluster_id': self.cluster_id, "node_status": node_list_result})

    def __node_services_status(self):
        node_list_rest_url = '/rest/node/list?columns=hostname'
        node_service_rest_url = '/rest/service/list?node={}'
        node_list_result = self.__call_rest_api(node_list_rest_url)
        result_list = []
        for node in node_list_result:
            node_name = node.get('hostname')
            services_list = self.__call_rest_api(
                node_service_rest_url.format(node_name))
            node_srv_list = []
            for service in services_list:
                node_srv_list.append({
                    'service_displayname': service.get('displayname'),
                    'status': service_status.get(service.get('state')),
                    'service_name': service.get('name')
                })
            result_list.append({node_name: node_srv_list})
        self.__update_result(
            {'cluster_id': self.cluster_id, "node_service_status": result_list})

    def __cldbs_status(self):
        cldbs_rest_url = '/rest/node/listcldbs'
        node_service_rest_url = '/rest/service/list?node={}'
        cldb_result = self.__call_rest_api(cldbs_rest_url)
        # print "=================="
        # print "Node CLDB Status\n=================="
        node_list = cldb_result[0].get('CLDBs').split(',')
        result_list = []
        for node_name in node_list:
            services_list = self.__call_rest_api(
                node_service_rest_url.format(node_name))
            for service in services_list:
                if service.get('name') == 'cldb':
                    result = {'node': node_name,
                              'service_displayname': service.get('displayname'),
                              'status': service_status.get(service.get('state')),
                              'service_name': service.get('name')
                              }
                    result_list.append(result)
        self.__update_result(
            {'cluster_id': self.cluster_id, "cldb_status": result_list})

    def __zookeeper_status(self):
        zkp_rest_url = '/rest/node/listzookeepers'
        zkp_result = self.__call_rest_api(zkp_rest_url)
        self.__update_result(
            {'cluster_id': self.cluster_id, "zookeepers": zkp_result[0]})

    def __yarn_details(self):
        dashboard_info_rest_url = '/rest/dashboard/info'
        cluster_list = self.__call_rest_api(dashboard_info_rest_url)
        result_list = []
        for cluster_info in cluster_list:
            yarn_info = cluster_info.get('yarn')
            result = {
                'cluster_id': cluster_info.get('cluster').get('id'),
                'cluster_name': cluster_info.get('cluster').get('name'),
                'num_of_yarn_node': yarn_info.get('num_node_managers'),
                'total_memory_mb': yarn_info.get('total_memory_mb'),
                'total_vcores': yarn_info.get('total_vcores'),
                'used_memory_mb': yarn_info.get('used_memory_mb'),
                'used_disks': yarn_info.get('used_disks'),
                'total_vcores': yarn_info.get('total_vcores'),
                'used_vcores': yarn_info.get('used_vcores')
            }
            result_list.append(result)
        self.__update_result(
            {'cluster_id': self.cluster_id, "cluster_yarn_details": result_list})

# Function Called by Poller Controller


def poll(meta={}, state={}):
    return HadoopClusterPoller(meta).poll()


if __name__ == '__main__':
    meta = dict({'cluster_ip': '192.168.100.205',
                 'username': 'mapr',
                 'password': 'mapr',
                 'port': 8443})
    result, status = poll(meta, None)
    print "RESULT :" + json.dumps(result)
    print "STATUS :" + json.dumps(status)
