from ..instances import InstanceBase
from ...core import *

class EndPointBase(Base):
    def __init__(self, context: Context, instance: InstanceBase, name=None):
        super().__init__(context, name, in_context=True)
        self.instance = instance

    def recv_request(self, host: str, endpoint: str, rc: RequestContext):
        raise NotImplementedError()
