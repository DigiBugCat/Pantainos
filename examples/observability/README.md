# Observability Example - Minimal Pantainos Application

This example shows how to create a simple observability application using Pantainos to collect and forward metrics.

## Features

- **HTTP Metrics Endpoint**: Receive metrics via REST API
- **Event-Driven Processing**: React to metrics using event handlers
- **Plugin Architecture**: Prometheus push gateway integration
- **Database Storage**: Event logging and variable storage
- **Minimal Dependencies**: Shows core Pantainos usage

## Usage

```python
from pantainos import Application, on_event
from plugins.prometheus import PrometheusPlugin

@on_event("metric.received")
async def log_metric(event):
    print(f"Received metric: {event.data}")

class ObservabilityApp(Application):
    def __init__(self):
        super().__init__(database_url="sqlite:///metrics.db")

        # Add Prometheus plugin
        prometheus = PrometheusPlugin(
            push_gateway_url="http://localhost:9091"
        )
        self.register_plugin(prometheus)

app = ObservabilityApp()
app.run()
```

## API

Send metrics to your application:

```bash
curl -X POST http://localhost:8000/metrics/push \
  -H "Content-Type: application/json" \
  -d '{"metric_name": "cpu_usage", "value": 85.5}'
```

## Installation

```bash
pip install pantainos
```

This example demonstrates the minimal Pantainos library usage without streaming-specific dependencies.
