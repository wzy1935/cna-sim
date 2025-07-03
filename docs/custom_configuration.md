# Custom Configuration

To make an object configurable, you need to create a `Config` class for it and register it with the `ContextBuilder`. Typically, the `Config` class is annotated with `@dataclass` and must implement two class methods:

- `from_json(cls, j, builder)`: Used to construct the `Config` object from a JSON object.

- `generator(self)`: Declares how to generate the target object from the `Config` instance.

To register your configuration with the context builder, call the `with_classes` method. Refer to the example below for usage.

For example, suppose we want to create a configuration for a `HelloWorld` component, which simply prints a message to the console at fixed intervals:

```python
class HelloWorld(Base):
    def __init__(self, context, message, interval, name=None):
        # ...
```

We want to make `message`, `interval`, and `name` configurable. So we define a `Config` like this:

```python
@dataclass
class HelloWorldConfig(Config):
    message: str
    interval: int
    name: str = None

    def generator(self):
        return lambda ctx: HelloWorld(ctx, self.message, self.interval, self.name)

    @classmethod
    def from_json(cls, j, builder):
        return HelloWorldConfig(**j)
```

Then register the `Config` class with the `ContextBuilder`:

```python
custom_builder = default_context_builder().with_classes([HelloWorldConfig])
```

Now you can use `custom_builder` to build a context that includes `HelloWorld`.

Sometimes, you may want to create a `Config` object on the fly without defining a full `Config` class. In such cases, you can use `Config.of()` to wrap a generator function. For example, you can quickly create a config for `HelloWorld` without using `HelloWorldConfig`:

```python
hello_world_config = Config.of(lambda ctx: HelloWorld(ctx, 'Hello world!', 1))
```
