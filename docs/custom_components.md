# Custom Components

CNASIM allows you to define your own custom components. For most components, e.g. `Instance`, `LoadGenerator`, `EndPoint`, we provide base classes that you can extend to implement your own logic. For example, to create a custom load balancer, you can extend the `ProxyBase` class. Here's a simple example:

```python
class RoundRobinLoadBalancer(ProxyBase):
    def __init__(self, context, service, name=None):
        super().__init__(context, name)
        self.service = service
        self.cur = 0

    def find_component(self, host: str, name: str = None, request: RequestContext = None):
        instances = [inst for inst in self.service.instances.values() if inst.metric('status') == 'ACTIVE']
        instances.sort(key=lambda x: x.name)
        self.cur = (self.cur + 1) % len(instances)
        return instances[self.cur]
```

Using a custom component works the same way as using a built-in one. Once you create an instance, it will automatically be registered to the context. In the case of a load balancer, the instance is typically created by the service, so you can attach your custom load balancer using a generator:

```python
service = Service(context,
    load_balancer_gen=lambda ctx, svc: RoundRobinLoadBalancer(ctx, svc),
    # ...
)
```

You can also create completely custom objects. If the object sends or receives requests, it should inherit from the `Agent` class. Otherwise, it should inherit from the `Base` class. This is because `Agent` supports network group declarations, while `Base` does not. For instance, an `Autoscaler` doesn’t handle message passing, so it inherits from `Base`; a `LoadGenerator`, however, does and therefore inherits from `Agent`.
Another difference is that `Agent` instances are automatically registered in the context by their name, while `Base` instances are not—unless you explicitly set `in_context=True`.

Here’s a simple example of a custom `HelloWorld` component that prints a message at regular intervals:

```python
class HelloWorld(Base):
    def __init__(self, context: Context, message, interval, name=None):
        super().__init__(context, name=name, in_context=True)
        self.message = not_none(message)
        self.interval = not_none(interval)
        self.run(self.process())

    def process(self):
        while True:
            yield self.timeout(self.interval)
            print(self.now(), self.message)


HelloWorld(context, 'Hello world!', 1, name='hello')
print(context['hello'])  # prints the HelloWorld instance
```
