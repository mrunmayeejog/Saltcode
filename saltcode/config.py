import os
import json

# User configurable settings via environment variables
filestore = os.environ.get('DEEPINSIGHT_FILESTORE_DIR') or os.path.join(
    os.path.expanduser('~/deepinsight'), '')

logs_dir = os.environ.get('DEEPINSIDE_LOGS_DIR') or os.path.join(
    os.path.expanduser('~/deepinsight'), 'logs')