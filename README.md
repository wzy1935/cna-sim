# CNASIM

CNASIM is a simulation framework designed for modeling cloud-native applications. It's built on SimPy, a framework that simulates events in a process-based system. CNASIM lets you model key components of cloud-native systems, such as services, instances, gateways, and load balancers. By defining applications and workloads in configuration files or scripts, you can run simulations to test the performance of your services without the need to actually deploy them. The results can exported to InfluxDB or any other data sinks of your choice.

With CNASIM, you can:

* Define the dependencies between services
* Simulate load balancing and autoscaling strategies
* Set thread and CPU resources for each instance
* Mimic network latency and failure situations
* Customize components and data exporters

## Getting Started

You can install CNASIM using pip locally:

```bash
pip install .
```

Check out the `/examples` directory for easy-to-understand examples. Running these scripts will help you get familiar with CNASIM and see how it works.




