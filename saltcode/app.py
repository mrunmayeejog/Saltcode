import os
from flask import request, session
from waitress import serve as waitress_serve
from flask import Flask
from jobhandler.restcontrollers.template_rest import post_upload, get_template
from jobhandler.restcontrollers.job_rest import start_job, kill_job
from jobhandler.restcontrollers.monitorning_rest import start_hadoop_monitoring, stop_hadoop_monitoring
app = Flask(__name__)

# REST APIs


@app.route('/deepinsight/v1/jobhandler/template/upload', methods=['POST'], strict_slashes=False)
def load():
    return post_upload()


@app.route('/deepinsight/v1/jobhandler/template/<template_id>', methods=['GET', 'DELETE'], strict_slashes=False)
def template(template_id):
    if request.method == 'DELETE':
        return delete_template(template_id)
    return get_template(template_id)

# REST APIs
# @app.route('/deepinsight/v1/jobhandler/template/<template_id>/<template_operation>', methods=['POST'], strict_slashes=False)
# def edit_template(template_id, template_operation):
#     return update_template(template_id, template_operation)
#
@app.route('/deepinsight/v1/jobhandler/template/<template_id>/job/start', methods=['POST'], strict_slashes=False)
def start_hadoop_job(template_id):
    return start_job(template_id)

@app.route('/deepinsight/v1/jobhandler/template/<template_id>/job/kill', methods=['POST'], strict_slashes=False)
def kill_hadoop_job(template_id):
    return kill_job(template_id)
#


@app.route('/deepinsight/v1/jobhandler/template/<template_id>/monitoring/start', methods=['POST'], strict_slashes=False)
def start_monitorning(template_id):
    return start_hadoop_monitoring(template_id)


@app.route('/deepinsight/v1/jobhandler/template/<template_id>/monitoring/stop', methods=['POST'], strict_slashes=False)
def stop_monitorning(template_id):
    return stop_hadoop_monitoring(template_id)


# Enable auto-reload of code if DEEPINSIGHT_AUTO_RELOAD environment variable is set.
# Useful in refreshing the demo site if new code is checked in.
def run_app():
    # setup_logging()
    # logging.info('Starting Deep Insight...')
    autoreload = os.environ.get('DEEPINSIGHT_AUTO_RELOAD')
    if autoreload == 'on':
        app.run(host='0.0.0.0', port=8080, threaded=True, debug=True)
    elif autoreload == 'off':
        # Use the production-ready WSGI Server instead
        # logging.info("Using waitress serving on port 8080")
        waitress_serve(app, host='0.0.0.0', port=8080)
    else:
        # Use the production-ready WSGI Server instead
        # logging.info("Using waitress serving on port 80")
        app.run(host='0.0.0.0', port=8080, threaded=True, debug=True)
        # waitress_serve(app, host='0.0.0.0', port=8080)


if __name__ == "__main__":
    run_app()
