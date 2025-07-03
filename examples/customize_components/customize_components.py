from dataclasses import dataclass

from cna_sim.core import Base, Context, Config
from cna_sim.builder import default_context_builder
from cna_sim.utils import not_none


"""
This is an example of a custom component that can be configured through a configuration file. It requires:

- Creating a custom config class to store the configuration information.
- Overriding the `generator` method so that the context can create the corresponding instance.
- Implementing the `from_json` method to define the format for reading from JSON or YAML.
- Registering the config class with the context builder.
"""

@dataclass
class MyComponentConfig(Config):
    name: str
    message: str
    interval: int

    def generator(self):
        return lambda ctx: MyComponent(ctx, self.message, self.interval, self.name)

    @classmethod
    def from_json(cls, j, builder):
        return MyComponentConfig(**j)


class MyComponent(Base):
    def __init__(self, context: Context, message, interval, name=None):
        super().__init__(context, name=name, in_context=True)
        self.message = not_none(message)
        self.interval = not_none(interval)
        self.run(self.process())

    def process(self):
        while True:
            yield self.timeout(self.interval)
            print(self.now(), self.message)


context = default_context_builder().with_classes([MyComponentConfig]).add_file('configuration.yaml').build()
print('You can assess the component object:', context.components['my_component'])
context.simulate(5)
context.close()

