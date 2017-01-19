'''
Mapr Hadoop job Poller to poll job level details

Prerequisites: Install python package using following command
                    pip install yarn-api-client==0.2.3
Parameter:
            {
            'resource_manager_address': <mapr-cluster-ip>,
            'port': <mapr-cluster-port>, # Port where cluster webserver running
            'application_tag': <tag>, # Fetch job based on tag provided while starting application
            'application_ids : <job-id-list>, # Fetch job based on tag provided while running application
            'application_names : <job-name-list>, # Fetch job based on tag provided while running application
            'application_status: 'running' # Fetch running jobs only 
            }
'''


from yarn_api_client import ApplicationMaster, HistoryServer, NodeManager, ResourceManager
import json


class HadoopJobPoller():

    _NAME_ = "Hadoop Job Poller"

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
        resource_manager_address = self.config.get('resource_manager_address')
        port = self.config.get('port')
        if port:
            self.resource_manager = ResourceManager(
                address=resource_manager_address, port=port)
            self.app_master = ApplicationMaster(
                address=resource_manager_address, port=port)
        else:
            self.resource_manager = ResourceManager(
                address=resource_manager_address)
            self.app_master = ApplicationMaster(
                address=resource_manager_address)
        self.application_ids = self.config.get('application_ids')
        self.application_status = self.config.get('application_status')
        self.application_tag = self.config.get('application_tag')
        self.application_names = self.config.get('application_names')
        self.application_status_list=[]

    def __update_result(self, result={}):
        self.result.append(result)

    def poll(self):
        try:
            self.__application_details()
            success_status = {
                "status": "COMPLETED",
                "status_message": "Hadoop Job poll completed successfully",
                "applications_status":self.application_status_list
            }
            return self.result, success_status

        except Exception as e:
            raise e
            exception_status = {
                "status": "EXCEPTION",
                "status_message": str(e)
            }

            return self.result, exception_status

    def __application_details(self):
        self.cluster_id = self.resource_manager.cluster_information(
        ).data.get('clusterInfo').get('id')
        app_list = self.resource_manager.cluster_applications().data.get('apps')
        app_result_list = []
        if app_list:
            for app in app_list.get('app'):

                if app.get('state').lower() == 'running':
                    jobs = (self.app_master.jobs(
                        app.get('id')).data.get('jobs').get('job'))
                    result_job_list = []
                    for job in jobs:
                        task = self.app_master.job_tasks(
                            app.get('id'), job.get('id')).data
                        job.update(task)
                        result_job_list.append(job)
                    app.update({"jobs": result_job_list})

                # Condition fetch application based on id
                if (self.application_names is not None) and (app.get('name') not in self.application_names):
                    continue

                # Condition fetch application based on id
                if (self.application_ids is not None) and (app.get('id') in self.application_id):
                    continue

                # Condition fetch application based on id
                if (self.application_status is not None) and (app.get('state').lower() != self.application_status):
                    continue

                # Condition fetch application based on id
                if (self.application_tag is not None) and (app.get('applicationTags').lower() != self.application_tag):
                    continue
                app_status = {'application_id': app.get('id'), 'application_name':app.get('name'),'status': app.get('state')}
                self.application_status_list.append(app_status)
                app_result_list.append(app)
        app_results = {'clusterId': self.cluster_id,
                       'applications': app_result_list}
        #self.__update_result(app_result_list)
        self.result = app_result_list

# Function Called by Poller Controller


def poll(meta={}, state={}):
    return HadoopJobPoller(meta).poll()

if __name__ == '__main__':
    import time
    config = dict(
        {'resource_manager_address': '192.168.100.205', 'port': 8088, 'application_names':['testdfsio_d3768577', "testdfsio_46c82af1"]})

    print config
    # yarn_plugin = HadoopJobPoller())
    result, status = poll(meta=config)  # yarn_plugin.poll()
    print "RESULT :" + json.dumps(result)
    print "STATUS :" + json.dumps(status)

