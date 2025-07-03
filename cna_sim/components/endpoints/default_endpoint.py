from . import EndPointBase
from ..instances import InstanceBase
from ...core import *

def sync_api(name: str):
    def decorator(func):
        func._api_path = name
        return func
    return decorator

def async_api(name: str):
    def decorator(func):
        func._api_path = name
        return func
    return decorator


class DefaultEndPoint(EndPointBase):
    def __init__(self, context: Context, instance, name=None):
        super().__init__(context, instance, name)
        self.endpoints = {}
        self._collect_apis()

    def _collect_apis(self):
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if callable(attr) and hasattr(attr, '_api_path'):
                path = getattr(attr, '_api_path')
                self.endpoints[path] = attr

    def recv_request(self, host: str, endpoint: str, rc: RequestContext):
        rc.proc_started = self.now()
        endpoint = self.endpoints[endpoint]
        try:
            response = yield self.run(endpoint(rc.request))
            rc.proc_success(response)
        except SimError as e:
            rc.fail(SimException('SERVER_DOWN'), True)
        except SimException as e:
            rc.fail(SimException('SERVER_ERROR'), True)

