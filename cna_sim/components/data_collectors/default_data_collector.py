from copy import copy
from dataclasses import dataclass

from . import DataCollectorBase
from ...core import *
import logging

@dataclass
class DefaultDataCollectorConfig(Config):
    name: str = None

    def generator(self):
        return lambda ctx: DefaultDataCollector(ctx, self.name)


class DefaultDataCollector(DataCollectorBase):
    def __init__(self, context: Context, name=None):
        super().__init__(context, name)

    def record_ended_request(self, rc: RequestContext):
        if not rc.mark:
            return
        # for k, v in {
        #     'req_sent': rc.req_sent,
        #     'req_arrived': rc.req_arrived,
        #     'proc_started': rc.proc_started,
        #     'proc_completed': rc.proc_completed,
        #     'resp_arrived': rc.resp_arrived,
        #     'failed_at': rc.failed_at
        # }.items():
        for k, v in {'req_sent': rc.req_sent}.items():
            if v is None:
                continue
            tags = {
                'host_name': rc.host_name,
                'instance_name': rc.instance_name,
                'endpoint_name': rc.endpoint_name,
                'status': 'TIMEOUT' if rc.is_timeout else rc.status,
                'timestamp_type': k
            }
            self.record('count', tags, {'value': 1}, v)
            if rc.req_arrived and rc.proc_started:
                self.record('queue_time', tags, {'value': rc.proc_started - rc.req_arrived}, v)
            if rc.proc_started and rc.proc_completed:
                self.record('computation_time', tags, {'value': rc.proc_completed - rc.proc_started}, v)
            if rc.resp_arrived and rc.req_sent:
                self.record('response_time', tags, {'value': rc.resp_arrived - rc.req_sent}, v)

    def record(self, measurement, tags, fields, time=None):
        if time is None:
            time = self.now()
        logging.info(f'{time, measurement, tags, fields}')

    def flush(self):
        pass

    def close(self):
        pass