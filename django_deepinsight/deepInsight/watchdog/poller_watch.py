from base_monitor import *


class PollerManager(BaseMonitor):
    _NAME_ = "pollers"

    def __init__(self, tid):
        super(PollerManager, self).__init__(PollerManager._NAME_, tid)

    def get_name(self):
        return self.name

    def deploy(self):
        pass

