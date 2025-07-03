from __future__ import annotations
import random
from copy import copy
from dataclasses import dataclass, field

from ..autoscalers import DefaultScalerConfig
from ...core import *
from ...utils import inject_context, default_if_none, not_none, shallow_asdict
from ..proxies import RandomLoadBalancerConfig


@dataclass
class ServiceConfig(Config):
    instance_config: Config
    load_balancer_config: Config = None
    autoscaler_config: Config = None
    replicas: int = None
    name: str = None
    network_group: str = None

    def generator(self):
        d = shallow_asdict(self)
        d['instance_gen'] = not_none(d.pop('instance_config', None)).generator()
        autoscaler_config = d.pop('autoscaler_config', None)
        d['autoscaler_gen'] = None if autoscaler_config is None else autoscaler_config.generator()
        load_balancer_config = d.pop('load_balancer_config', None)
        d['load_balancer_gen'] = None if load_balancer_config is None else load_balancer_config.generator()
        return lambda ctx: Service(ctx, **d)

    @classmethod
    def from_json(cls, j, builder):
        j = copy(j)
        j['instance_config'] = builder.use_config(j.get('instance_config'))
        j['load_balancer_config'] = builder.use_config(j.get('load_balancer_config'))
        j['autoscaler_config'] = builder.use_config(j.get('autoscaler_config'))
        return ServiceConfig(**j)


class Service(Agent):
    def __init__(self, context: Context, instance_gen, load_balancer_gen=None, autoscaler_gen=None, replicas=None, name=None, network_group=None):
        super().__init__(context, name, network_group)
        self.instances = {}  # will only contain STARTING and ACTIVE
        self.instance_gen = not_none(instance_gen)
        self.load_balancer = default_if_none(load_balancer_gen, RandomLoadBalancerConfig().generator())(context, self)
        self.autoscaler = default_if_none(autoscaler_gen, DefaultScalerConfig().generator())(context, self)
        self.scale_to(default_if_none(replicas, 1))

        self.run(self.monitoring())

    def scale_to(self, instances: int):
        delta = instances - len(self.instances)
        if delta >= 0:
            for _ in range(delta):
                new_instance = inject_context(self.instance_gen, self.context, self)
                new_instance.service_name = self.name
                self.instances[new_instance.name] = new_instance
        else:
            for _ in range(-delta):
                not_init = [k for k, v in self.instances.items() if v.metric('status') == 'STARTING']
                if not_init:
                    k = random.choice(not_init)
                else:
                    k = random.choice(list(self.instances.keys()))
                self.instances[k].terminate()
                del self.instances[k]

    def recv_request(self, host, endpoint, request_context):
        component = self.load_balancer.find_component(host, endpoint, request_context.request)
        if component is None:
            request_context.fail(SimException('CONNECTION_REFUSED'), True)
        else:
            component.recv_request(host, endpoint, request_context)

    def metric(self, name):
        if name == 'active_instance_num':
            return len([x for x in self.instances.values() if x.metric('status') == 'ACTIVE'])
        if name == 'instance_num':
            return len(self.instances)

    def monitoring(self):
        while True:
            tags = {
                'host_name': self.name,
            }
            self.context.data_collector.record('instance_num', tags, {'value': self.metric('instance_num')})
            self.context.data_collector.record('active_instance_num', tags,
                                               {'value': self.metric('active_instance_num')})
            yield self.timeout(1)
