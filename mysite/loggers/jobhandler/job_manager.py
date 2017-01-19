#!/usr/bin/env python
import salt.client
import os


def start_yarn_application(template_id, resource_manager, mapr_user='mapr', job_details={}, tag=None, parameter=None):
    print template_id, resource_manager, mapr_user, job_details, tag, parameter
    job_type = job_details.get('job_type', None)
    job_name = job_type + '_' + os.urandom(4).encode('hex')
    try:
        if job_type:
            if tag:
                job_tag = '-Dmapreduce.job.tags={}'.format(tag)
            job_name_tag = '-Dmapreduce.job.name={}'.format(job_name)

            # TestDFSIO
            if job_type.lower() == 'testdfsio':
                jar_name = '/opt/mapr/hadoop/hadoop-0.20.2/hadoop-0.20.2-dev-test.jar'
                test_name = 'TestDFSIO'
                if tag:
                    job_cmd = 'yarn jar {} {} {} {} -write -nrFiles 30 -fileSize 2048'.format(
                        jar_name, test_name, job_name_tag, job_tag)
                else:
                    job_cmd = 'yarn jar {} {} {} -write -nrFiles 30 -fileSize 2048'.format(
                        jar_name, test_name, job_name_tag)

                yarn_command = 'su -l {} -c "{}"'.format(mapr_user, job_cmd)
            '''
            if job_type.lower() == 'terasort':
                cmd_delete_terasort_input_dir = "hadoop fs -rm -r -f -skipTrash /terasort-input;"
                cmd_to_start_terasort = " hadoop jar /opt/mapr/hadoop/hadoop-0.20.2/hadoop-0.20.2-dev-examples.jar teragen -Dmapreduce.job.tags={} 100000 /terasort-input".format(
                    tag)
                yarn_command = cmd_delete_terasort_input_dir + cmd_to_start_terasort
            if job_type.lower() == 'teragen':
                cmd_delete_teragen_output_dir = "hadoop fs -rm -r -f -skipTrash /terasort-output;"
                cmd_to_start_teragen = " hadoop jar /opt/mapr/hadoop/hadoop-0.20.2/hadoop-0.20.2-dev-examples.jar terasort -Dmapreduce.job.tags={} /terasort-input /terasort-output".format(
                    tag)
                yarn_command = cmd_delete_teragen_output_dir + cmd_to_start_teragen
            '''

            salt_client = salt.client.LocalClient()
            # Execute YARN JOB
            salt_client.cmd(resource_manager, fun="cmd.run_bg",
                            arg=[yarn_command])
            return job_name
    except Exception as e:
        raise e


def kill_yarn_application(resource_manager, application_id):

    if application_id and resource_manager:
        yarn_kill_command = 'yarn application -kill {}'.format(application_id)
        salt_client = salt.client.LocalClient()
        result = salt_client.cmd(
            resource_manager, fun="cmd.run", arg=[yarn_kill_command])

        print "YARN KILL SALT RESPONSE : " + str(result)
        if 'java.lang.IllegalArgumentException: Invalid ApplicationId prefix: {}'.format(application_id) in result.get(resource_manager):
            raise Exception(
                'Application ID <{}> not found'.format(application_id))

        if 'Killed application {}'.format(application_id) in result.get(resource_manager):
            return "Application <{}> killed successfully".format(application_id)

        if '{} has already finished'.format(application_id) in result.get(resource_manager):
            return "Application <{}> has already finished".format(application_id)

    else:
        raise Exception('application_id is None')

if __name__ == '__main__':

    print kill_yarn_application('mapr-node1', application_id="application_1482480301899_0018")
