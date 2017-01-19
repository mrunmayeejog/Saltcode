#!/usr/bin/env python
import salt.client
import json
import sys, os
import re

SERVICE_STATUS = {'available': 'service.available',
                    'restart': 'service.restart',
                    'start': 'service.start',
                    'stop': 'service.stop',
                    'status': 'service.status' }

class SaltManager():

    def change_service_status(self, nodes, services, status):
        # Change the service status to user provided value.
        local = salt.client.LocalClient()
        status = local.cmd(tgt=nodes, expr_form='list', fun=SERVICE_STATUS[status],
                               arg=services)
        return status

    def delete_files(self, file_list=[], dest_nodes=[]):
        status_delete = {}
        for node in dest_nodes:
            status_delete[node] = {}
            status_delete[node]["success_list"] = []        
            status_delete[node]["failed_list"] = []
        try:
            local = salt.client.LocalClient()
            for file in file_list:
                cmd_string = "rm " + file
                status = local.cmd(tgt=dest_nodes, expr_form='list',
                                  fun="cmd.run", arg=[cmd_string])
                for node in dest_nodes:
                    if node in status:
                        if file == "*.conf":
                            status_delete[node]["success_list"].append(file)
                            continue
                        if status[node].startswith("rm"):
                            status_delete[node]["failed_list"].append(file)
                        else:
                            status_delete[node]["success_list"].append(file)
                    else:
                        status_delete[node]["failed_list"].append(file)
        except Exception as e:
            print e
        return status_delete


    def reset_logger_config(self,disable_plugins=[],dest_nodes=[]):
        local = salt.client.LocalClient()
        new_config =  os.path.sep + 'etc' + os.path.sep + 'td-agent'+ os.path.sep + 'td-agent.conf'
        content =  local.cmd(tgt=dest_nodes, expr_form='list', fun="cp.get_file_str", arg=[new_config])

        existing_plugins = content.values()[0].split('\n\n')[0].split('\n')
        default_match = content.values()[0].split('\n\n')[1].split('\n')

        for x_plugin in disable_plugins:
            if "@include "+ x_plugin in existing_plugins:
                 existing_plugins.remove("@include "+ x_plugin)
 
        existing_plugins.append('\n')
        all_content = existing_plugins + default_match
        return '\n'.join(all_content).replace('\n\n', '\n')
 

    def push_config(self, cfg_info_list=[], dest_nodes=[]):
        status_push = {}
        for node in dest_nodes:
            status_push[node] = {}
            status_push[node]["success_list"] = []        
            status_push[node]["failed_list"] = []
        try:
            local = salt.client.LocalClient()
            for cfg_info in cfg_info_list:
                config = cfg_info[1]
                dest_file = cfg_info[0]
                status = local.cmd(tgt=dest_nodes, expr_form='list',
                                  fun="file.write", arg=[dest_file, config])
                for node in dest_nodes:
                    if node in status:
                        if status[node].startswith("Wrote"):
                            status_push[node]["success_list"].append(dest_file)  
                            continue
                    status_push[node]["failed_list"].append(dest_file) 
        except Exception as e:
            print e
        return status_push

