#!/usr/bin/env python

from operator import attrgetter
import acitoolkit.acitoolkit as ACI
import json
from pprint import pprint


def get_vlan_detail(session):
    """
    get_vlans queries all the nodes from APIC and collects VLAN
    details from each of the node.

    :param session:
    :return: List
     Example:      [ {
                      'id': '101',
                      'data': [
                               {
                                 'vlan': 13,
                                 'name': vlan13
                                 'status': 'active',
                                 'ports': ['eth1/41', 'eth1/41']
                               }]
                    }]
    """
    nodes = []
    res = []
    node_ids = []
    # node_details return the data
    node_details = []

    # URL to get the registered nodes in APIC
    query_url = ('/api/node/class/fabricNode.json?query-'
                 'target-filter=eq(fabricNode.role,"leaf")')
    resp = session.get(query_url)
    if not resp.ok:
        raise Exception('Could not get switch list from APIC.')
    nodes = resp.json()['imdata']
    for node in nodes:
        node_ids.append(str(node['fabricNode']['attributes']['id']))

    for node_id in node_ids:
        query_url = ('/api/mo/topology/pod-1/node-%s.json?query-target=subtr'
                     'ee&target-subtree-class=l2BD,l2RsPathDomAtt' % node_id)
        resp = session.get(query_url)
        if resp.ok:
            nodedata = {}
            l2bd_data = []
            port_data = {}
            for obj in resp.json()['imdata']:
                if 'l2BD' in obj:
                    obj_attr = obj['l2BD']['attributes']
                    l2bd_data.append((int(obj_attr['id']), str(obj_attr['name']),
                                      str(obj_attr['adminSt']),
                                      str(obj_attr['fabEncap'])))
                else:
                    dn = obj['l2RsPathDomAtt']['attributes']['dn']
                    port_id = str(dn.rpartition(
                        '/path-[')[2].partition(']')[0])
                    port_bd_encap = str(dn.partition(
                        '/bd-[')[2].partition(']')[0])
                    if port_bd_encap not in port_data:
                        port_data[port_bd_encap] = port_id
                    port_data[port_bd_encap] += ', ' + port_id
            output_data = []
            for (l2bd_id, l2bd_name, l2bd_admin_state, l2bd_fab_encap) in l2bd_data:
                try:
                    ports = port_data[str(l2bd_fab_encap)]
                except KeyError:
                    ports = ''
                output_data.append(
                    (l2bd_id, l2bd_name, l2bd_admin_state, ports))
            output_data.sort(key=lambda tup: tup[0])

            nodedata['id'] = node_id
            nodedata['data'] = []
            for data in output_data:
                vlan_detail = {}
                vlan_detail["ports"] = data[3].split(',')
                vlan_detail["vlanid"] = data[0]
                vlan_detail["status"] = data[2]
                nodedata['data'].append(vlan_detail)

            node_details.append(nodedata)
    return node_details


def show_stats_short(session, meta, interfaces, granularity, epoch):
    """
    show stats short routine
    :param session: A session to login to APIC
    :param meta: metadata in JSON format
    :param interfaces: list of interfaces
    :param granularity: interval ex: 5min, 15min, 1h etc
    :param epoch: The <epoch> is an integer representing which set of
                  historical stats you want to reference
    :return: list of dictionaries with results
    """

    counter_list = []
    for counter_family in meta["stats_family"]:
        for counter_name in counter_family["family_sub_type"]:
            temp_family = (counter_family["family_name"], counter_name)
            counter_list.append(temp_family)

    # List to hold the result dictionaries
    rec = []

    # Loop over interfaces to add all the details of the individual interface
    for interface in sorted(interfaces, key=attrgetter('if_name')):
        interface.stats.get()
        # print interface.name

        for (counter_family, counter_name) in counter_list:
            # Dictionary to hold the individual interface parameters
            result = {}
            result["interface_name"] = interface.name
            result["counter_family"] = counter_family
            result["counter_name"] = counter_name
            result["value"] = interface.stats.retrieve(counter_family,
                                                       granularity, epoch,
                                                       counter_name)
            result["admin_status"] = interface.adminstatus
            result["operational_status"] = interface.attributes["operSt"]
            result["pod"] = interface.pod
            result["module"] = interface.module
            result["port"] = interface.port
            result["node"] = interface.node
            result['vlan_id'] = None
            rec.append(result)

    nodes = get_vlan_detail(session)
    for node in nodes:
        for interface in rec:
            if node['id'] == interface['node']:
                for nodedata in node['data']:
                    for port in nodedata['ports']:
                        if port.strip('eth') in interface['interface_name']:
                            interface['vlan_id'] = nodedata['vlanid']

    return rec


def is_valid(interface):
    if len(interface.split('/')) != 4:
        return False
    else:
        (pod, node, module, port) = interface.split('/')
        try:
            int(pod)
            int(node)
            if len(node) != 3:
                raise ValueError("Invalid Node")
            int(module)
            int(port)
        except ValueError:
            return False

        return True


def poll(meta, state):
    """
    Parse the JSON and get the information
    """
    url = "https://" + str(meta["apic_ip_addres"])
    # print url
    username = meta["credentials"]["username"]
    password = meta["credentials"]["password"]
    #input_interface = meta["interface"]

    interface_list = meta["interface"]

    granularity = meta["granularity"]
    epoch = 0

    # Login to APIC
    session = ACI.Session(url, username, password)
    resp = session.login()

    state = {}
    result = []

    state['status'] = None
    state['message'] = None
    state['error'] = None
    if not resp.ok:
        state['status'] = resp.status_code
        state['error'] = "Login failed"
        state['message'] = "Could not login to APIC"
        return result, state

    if "all" in interface_list:
        if not (1 == len(interface_list)):
            state['message'] = ("Invalid input, interface list should "
                                "contain all or specific interface names.")
            state['error'] = "Invalid interface list"
            state['status'] = resp.status_code
        else:
            interfaces = ACI.Interface.get(session)
            result = show_stats_short(session, meta, interfaces, granularity,
                                      epoch)
            state['message'] = "Successfully pulled all interface stats"
            state['error'] = "None"
            state['status'] = resp.status_code
    else:
        for interface in interface_list:
            if is_valid(interface):
                if 'eth ' in interface:
                    interface = interface[4:]
                (pod, node, module, port) = interface.split('/')

                # convert to string, as get method expects pod, node,module,
                # port in string format
                pod = str(pod)
                node = str(node)
                module = str(module)
                port = str(port)
                iface = ACI.Interface.get(session, pod, node, module, port)
                res = show_stats_short(session, meta, iface, granularity,
                                       epoch)
                for i in res:
                    result.append(i)

                state['message'] = "Successfully pulled interface stats"
                state['error'] = "None"
                state['status'] = resp.status_code
            else:
                state['message'] = "Invalid interface name found : %s" % (
                    interface)
                state['error'] = "Invalid interface name"
                state['status'] = resp.status_code
                break

    return result, state

"""
def main():
    with open('aci_poller_meta_sample.json') as input_meta:
        meta = json.load(input_meta)

        state = {}
        result, state = poll(meta, state)
        pprint(result)
        pprint(state)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
"""
