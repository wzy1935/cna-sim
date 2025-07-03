from ...core import *

class DataCollectorBase(Base):
    def __init__(self, context: Context, name=None):
        super().__init__(context, name, in_context=True)

    def record_ended_request(self, rc: RequestContext):
        raise NotImplementedError()

    def record(self, measurement, tags, fields, time=None):
        raise NotImplementedError()

    def flush(self):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()