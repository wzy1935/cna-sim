from dataclasses import dataclass
from copy import copy
import simpy
from ...core import *
from .instance_base import InstanceBase
from ...utils import remove_m, inject_context, not_none, default_if_none, shallow_asdict


class ThreadPool(Base):
    def __init__(self, context: Context, threads: int):
        super().__init__(context)
        self.threads = simpy.Container(context.env, threads, threads)
        self.active_threads = 0
        self.active_threads_track = []
        self.run(self.monitoring())

    def monitoring(self):
        while True:
            yield self.timeout(0.1)
            self.active_threads_track.append(self.active_threads)
            self.active_threads_track = self.active_threads_track[-20:]

@dataclass
class SyncServerConfig(Config):
    endpoint_config: Config
    cpu_quota: float = None
    threads: int = None
    queue_size: int = None
    name: str = None
    service_name: str = None
    network_group: str = None
    start_up_delay: float = None
    warming_up_time: float = None
    warming_up_factor_init: float = None
    shut_down_delay: float = None

    def generator(self):
        def sync_server_gen(ctx, svc=None):
            d = shallow_asdict(self)
            endpoint_config = not_none(d.pop('endpoint_config', None))
            d['endpoint_gen'] = endpoint_config.generator()
            if svc is not None and d.get('service_name') is None:
                d['service_name'] = svc.name
            return SyncServer(ctx, **d)
        return sync_server_gen

    @classmethod
    def from_json(cls, j, builder):
        j = copy(j)
        j['endpoint_config'] = builder.use_config(j.get('endpoint_config'))
        j['cpu_quota'] = remove_m(j.get('cpu_quota'))
        return cls(**j)


class SyncServer(InstanceBase):
    def __init__(self, context, endpoint_gen, cpu_quota=None, threads=None, queue_size=None, name=None, service_name=None, network_group=None,
                 start_up_delay=None, warming_up_time=None, warming_up_factor_init=None, shut_down_delay=None):
        super().__init__(context, name, service_name, network_group)
        self.endpoints = inject_context(not_none(endpoint_gen), self.context, self)
        self.queue = simpy.Store(context.env)
        self.cpu_quota = default_if_none(cpu_quota, 1)
        self.queue_size = queue_size # can be none
        self.start_up_delay = default_if_none(start_up_delay, 0)
        self.warming_up_time = default_if_none(warming_up_time, 0)
        self.warming_up_factor_init = default_if_none(warming_up_factor_init, 2)
        self.shut_down_delay = default_if_none(shut_down_delay, 60)
        self.threads = ThreadPool(context, default_if_none(threads, 32))

        self.client = Client(context, owner=self)
        self.start_time = self.now()
        self.status = 'STARTING' # could be ['STARTING', 'ACTIVE', 'TERMINATING', 'TERMINATED']
        self.alive = self.context.env.event()
        self.init(self.start_up_delay)
        self.run(self.process())
        self.run(self.monitoring())

    def recv_request(self, host, endpoint, request_context):
        if self.alive.triggered:
            return
        request_context.instance_name = self.name
        request_context.req_arrived = self.now()
        if self.status not in ['ACTIVE', 'TERMINATING'] or self.queue_size and len(self.queue.items) >= self.queue_size:
            request_context.fail(SimException('CONNECTION_CLOSED'), True)
        else:
            self.queue.put((host, endpoint, request_context))

    def process(self):
        while not self.alive.triggered:
            host, name, request_promise = yield self.queue.get()
            yield self.threads.threads.get(1)

            def _(host, name, request_promise):
                yield self.run(self.endpoints.recv_request(host, name, request_promise))
                self.threads.threads.put(1)

            self.run(_(host, name, request_promise))

    def warming_up_factor(self):
        t = self.now() - self.start_time - self.start_up_delay
        wut = self.warming_up_time
        wufi = self.warming_up_factor_init
        if t <= 0:
            return wufi
        elif t < wut:
            return wufi + (1 - wufi) * (t / wut)
        else:
            return 1.0


    def compute(self, cpu_time):
        def _(cpu_time):
            t = cpu_time.sample()
            self.threads.active_threads += 1
            try:
                t = t * max(1.0, self.threads.active_threads / self.cpu_quota) * self.warming_up_factor()
                yield self.alive_race(self.timeout(t), self.alive)
            except SimError as e:
                raise e
            finally:
                self.threads.active_threads -= 1

        return self.run(_(cpu_time))

    def send_request(self, host, endpoint, request, timeout=None):
        request_promise = self.client.send_request(host, endpoint, request, timeout)
        # TODO: instance could terminate here
        return request_promise

    def init(self, delay=.0):
        def _(delay=delay):
            yield self.timeout(delay)
            if self.status == 'STARTING':
                self.status = 'ACTIVE'
        self.run(_())

    def terminate(self):
        self.status = 'TERMINATING'
        def _():
            yield self.timeout(self.shut_down_delay)
            for host, name, request_context in self.queue.items:
                request_context.fail(SimException('SERVER_DOWN'), True)
            self.queue.items.clear()
            self.alive.succeed(SimError('THIS_DOWN'))
            self.status = 'TERMINATED'
        self.run(_())

    def cpu_usage(self):
        threads_track = self.threads.active_threads_track[-10:]
        if not threads_track:
            return 0.0
        cpu_track = [min(x, self.cpu_quota) for x in threads_track]
        return float(sum(cpu_track) / len(cpu_track))

    def metric(self, name):
        if name == 'status':
            return self.status
        if self.status in ['ACTIVE']:
            if name == 'cpu_usage':
                return self.cpu_usage()
            if name == 'cpu_utilization':
                return self.cpu_usage() / self.cpu_quota
            if name == 'active_threads':
                return self.threads.active_threads

    def monitoring(self):
        while not self.alive.triggered:
            tags = {
                'host_name': self.service_name,
                'instance_name': self.name
            }
            self.context.data_collector.record('cpu_usage', tags, {'value': self.metric('cpu_usage')})
            self.context.data_collector.record('active_threads', tags, {'value': self.metric('active_threads')})
            yield self.timeout(1)
