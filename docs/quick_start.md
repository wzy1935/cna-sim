# Quick Start

A basic simulation generally consists of the following steps:

* Initialize the Context and components
* Register runtime events
* Run the simulation

## Initialization

During initialization, you need to create a `Context` for the simulation. A `Context` represents the execution environment of a simulation, and you need to bind the components to it. Components are automatically bound upon creation. Here is an example:

```python
context = ContextConfig().generate()
load_generator = RPSLoadGenerator(
    context, 
    proxy=context.gateway, 
    rps=10, 
    host='my_service', 
    endpoint='/my_endpoint'
)
```

The code above creates a context and binds a load generator instance to it. When the simulation starts, this instance will send 10 requests per simulated second.

Typically, you also need to add a data collector during initialization to specify how and where to export data. You can configure it in `ContextConfig`. If not configured, the default data collector will output logs to the command line at the INFO level. You can enable it with the `logging` library:

```python
logging.basicConfig(level=logging.INFO)
```

## Registering Runtime Events

You can modify the simulation during runtime. Use the `context.run` method to register functions or generators that should be executed:

```python
def change_rps():
    yield context.timeout(10)
    load_generator.rps = 20

context.run(change_rps())
```

`context.run` executes from the current simulation time. The time at initialization is 0. After registration, when the simulation reaches 10 simulated seconds, the load generator's RPS will be changed to 20.

## Running the Simulation

Use the `context.simulate` method to run the simulation. The following code runs the simulation until 60 simulated seconds:

```python
context.simulate(until=30)
context.close()
```

Check the full example at `/examples/quick_start`.
