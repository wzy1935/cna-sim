import yaml
import os

from .components.autoscalers import DefaultScalerConfig, HorizontalAutoscalerConfig
from .components.data_collectors import DefaultDataCollectorConfig, InfluxDataCollectorConfig
from .components.endpoints import StaticEndPointConfig
from .components.instances import SyncServerConfig
from .components.load_generators import RPSLoadGeneratorConfig, DynamicRPSLoadGeneratorConfig
from .components.networks import DefaultNetworkConfig
from .components.proxies import GatewayConfig, RandomLoadBalancerConfig
from .components.services import ServiceConfig
from .core import ContextConfig, Context
from .utils import default_if_none, uuid


class ContextBuilder:
    def __init__(self):
        self.class_templates = {}
        self.config_jsons = {}

    def with_classes(self, config_class_list):
        self.class_templates = {**self.class_templates, **{x.kind(): x for x in config_class_list}}
        return self

    def use_config(self, name):
        if name is None:
            return None
        config_json = self.config_jsons[name]
        clazz = self.class_templates[config_json['kind']]
        config = clazz.from_json(default_if_none(config_json.get('spec'), {}), self)
        return config

    def add_config_json(self, config_json):
        if config_json.get('name') is None:
            config_json['name'] = uuid()
        self.config_jsons[config_json['name']] = config_json
        return self

    def add_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load_all(f)
            for d in data:
                if d is None:
                    continue
                self.add_config_json(d)
        return self

    def add_folder(self, folder_path):
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith(('.yaml', '.yml')):
                    file_path = os.path.join(root, file)
                    self.add_file(file_path)
        return self

    def build(self) -> Context:
        for k, v in self.config_jsons.items():
            if v['kind'] == 'ContextConfig':
                context_config_json = v
                break
        else:
            raise Exception('ContextConfig not found.')

        context_config = ContextConfig.from_json(default_if_none(context_config_json.get('spec'), {}), self)
        return context_config.generate()


def default_context_builder():
    return ContextBuilder().with_classes([
        ContextConfig,
        DefaultScalerConfig, HorizontalAutoscalerConfig,
        DefaultDataCollectorConfig, InfluxDataCollectorConfig,
        StaticEndPointConfig,
        SyncServerConfig,
        RPSLoadGeneratorConfig, DynamicRPSLoadGeneratorConfig,
        DefaultNetworkConfig,
        GatewayConfig, RandomLoadBalancerConfig,
        ServiceConfig,
    ])
