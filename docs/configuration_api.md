# Configuration API

## Configure by YAML

Any object wrapped by `Config` can be generated together when creating a context using a static configuration file. Use `ContextBuilder` to generate objects from a configuration file:

```python
context = default_context_builder().add_folder('./your_configs').build()
```

The format of the configuration file is as follows:

```yaml
kind: str
name: str
spec:
    ...
```

- `kind` specifies the configuration class of the component you want to use, usually directly the class name.

- `name` declares the name of the configuration, which can be left empty. It is used when one configuration refers to another.

- `spec` contains the specific configuration details. Refer to the fields of the corresponding configuration class for more information. For example, the class declaration of `ServiceConfig` is as follows:

```python
@dataclass
class ServiceConfig(Config):
    instance_config: Config
    load_balancer_config: Config = None
    autoscaler_config: Config = None
    replicas: int = None
    name: str = None
    network_group: str = None
```

Then, the configuration file can be written like this:

```yaml
kind: ServiceConfig
name: service_config
spec:
  name: service_example
  instance_config: pod_example_config
  autoscaler_config: autoscaler_example_config
  replicas: 3
```

Note that when a configuration needs to reference other configurations, it is represented by the name of the referenced configuration in the file. In this example, `service_config` will use the configuration named `pod_example_config` as the `instance_config` parameter.

If you want the components specified in the configuration to be created along with the context, you need to include the configuration name in a `ContextConfig`:

```yaml
kind: ContextConfig
name: context_config
spec:
  component_configs:
    - service_config
```

A `ContextConfig` is required when `ContextBuilder` generates a context; it defines the basic information.

## Configure by Scripts

The Configuration API can also be used in scripts. The `Config` class has two methods: `generator()` and `generate()`.

- `generator()` returns a lambda function that acts as a generator for the target component, typically with the context as an input.

- `generate()` is a shortcut that calls the `generator()` directly.

Here's an example that creates an `endpoint` object and binds it to an `instance`:

```python
# use generator()
endpoint_generator = StaticEndPointConfig([('/example', [], Distribution(0.1))]).generator() # lambda ctx, ins: StaticEndPoint(...)
endpoint = endpoint_generator(context, instance)

# use generate()
endpoint = StaticEndPointConfig([('/example', [], Distribution(0.1))]).generate(context, instance)
```

