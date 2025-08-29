# 🔍 Observability Plugin Example

A complete example demonstrating Pantainos plugin capabilities with a full web interface for observability and metrics tracking.

## ✨ Features

- **📊 Web Dashboard** - Real-time metrics visualization
- **🔌 Plugin Architecture** - Clean, extensible plugin design
- **📡 REST API** - Event submission via HTTP POST
- **⚡ Real-time Updates** - Live metrics tracking
- **🎛️ Configuration Interface** - Web-based plugin configuration
- **📈 Event History** - Track and display recent events

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install aiohttp for the event submission script
uv add aiohttp --dev
```

### 2. Start the Application

```bash
# From the project root
uv run python examples/observability_plugin/main.py
```

You should see output like:
```
🚀 Starting Pantainos Observability Plugin Example
============================================================
🔍 Observability Plugin started
✅ Application started successfully!

🌐 Web Interface Available:
   • Main Dashboard: http://localhost:8080
   • Plugin Dashboard: http://localhost:8080/ui/plugins/observability
   • Plugin Config: http://localhost:8080/ui/plugins/observability/config
```

### 3. Submit Test Events (Optional)

In another terminal:

```bash
uv run python examples/observability_plugin/send_events.py
```

## 🌐 Web Interface

### Main Dashboard
Visit `http://localhost:8080` to see the main application dashboard.

### Plugin Dashboard
Visit `http://localhost:8080/ui/plugins/observability` to see:

- **Real-time Metrics**: Events received, HTTP requests, errors
- **Status Information**: Plugin status and uptime
- **Recent Events**: Live feed of the latest events
- **Visual Design**: Clean, responsive interface

### Configuration Page
Visit `http://localhost:8080/ui/plugins/observability/config` for:

- **Current Settings**: Plugin configuration and status
- **API Documentation**: Available endpoints and usage
- **Example Requests**: Copy-paste curl commands

## 📡 REST API Endpoints

### Submit Events
```bash
POST /api/observability/events
Content-Type: application/json

{
  "event_type": "http.request",
  "data": {
    "path": "/api/users",
    "status": 200,
    "method": "GET"
  }
}
```

### Get Metrics
```bash
GET /api/observability/metrics
```

Response:
```json
{
  "events_received": 42,
  "http_requests": 15,
  "errors": 2,
  "status": "active",
  "last_event_time": "2024-01-15T10:30:45.123456",
  "event_history": ["..."]
}
```

### Reset Metrics
```bash
POST /api/observability/metrics/reset
```

## 💡 Example Usage

### Basic Event Submission

```bash
# HTTP request event
curl -X POST http://localhost:8080/api/observability/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "http.request",
    "data": {"path": "/api/test", "status": 200, "method": "GET"}
  }'

# Error event
curl -X POST http://localhost:8080/api/observability/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "error",
    "data": {"message": "Database timeout", "component": "database"}
  }'

# Custom metric
curl -X POST http://localhost:8080/api/observability/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "metric.update",
    "data": {"name": "cpu_usage", "value": 75.2, "unit": "%"}
  }'
```

### View Results
After submitting events, visit the web dashboard to see:
- Updated counters
- Recent event feed
- Real-time status information

## 🏗️ Architecture

### Plugin Structure
```
examples/observability_plugin/
├── plugin.py          # Main plugin with web pages and API
├── main.py            # Application setup and event handlers
├── send_events.py     # Event submission utility
└── README.md          # This file
```

### Key Components

**ObservabilityPlugin** (`plugin.py`)
- Extends `Plugin` base class
- Implements `@plugin.page()` and `@plugin.api()` decorators
- Manages metrics storage and event history
- Provides web interface pages with HTML/CSS

**Application Setup** (`main.py`)
- Creates Pantainos app with web dashboard enabled
- Mounts the observability plugin
- Sets up event handlers for different event types
- Demonstrates plugin integration patterns

**Event Submitter** (`send_events.py`)
- HTTP client for testing API endpoints
- Demonstrates various event types
- Shows real-world usage patterns

## 🎯 What This Demonstrates

### Plugin Development
- ✅ Creating custom plugins with web interfaces
- ✅ Using `@plugin.page()` decorator for web pages
- ✅ Using `@plugin.api()` decorator for REST endpoints
- ✅ Plugin lifecycle management (start/stop)
- ✅ Event emission from plugins

### Web Interface Integration
- ✅ Automatic plugin page mounting
- ✅ HTML/CSS integration in plugins
- ✅ REST API endpoint registration
- ✅ Real-time data display

### Event-Driven Architecture
- ✅ Event handlers with dependency injection
- ✅ Plugin-to-plugin communication via events
- ✅ HTTP POST event submission
- ✅ Event history and metrics tracking

### Production Patterns
- ✅ Configuration via constructor parameters
- ✅ Proper error handling and logging
- ✅ Clean separation of concerns
- ✅ Comprehensive API documentation

## 🔧 Customization

### Adding New Event Types
1. Add handler in `main.py`:
```python
@app.on("custom.event")
async def handle_custom_event(event) -> None:
    # Process the event
    obs_plugin.metrics["custom_events"] += 1
```

2. Update metrics display in `plugin.py` dashboard

### Extending the Web Interface
1. Add new pages:
```python
@plugin.page("analytics")
async def analytics_page():
    return """<div>Custom analytics dashboard</div>"""
```

2. Add new API endpoints:
```python
@plugin.api("/custom-endpoint")
async def custom_endpoint():
    return {"custom": "data"}
```

### Modifying Metrics
Update the `metrics` dictionary in `ObservabilityPlugin.__init__()`:
```python
self.metrics = {
    "events_received": 0,
    "custom_metric": 0,
    # ... add more metrics
}
```

## 📚 Next Steps

- **Scale Up**: Add database persistence for metrics
- **Real-time**: Implement WebSocket for live updates
- **Dashboards**: Create more sophisticated visualizations
- **Alerting**: Add threshold-based notifications
- **Authentication**: Secure the web interface
- **Monitoring**: Add health checks and status endpoints

---

This example provides a complete foundation for building production observability systems with Pantainos! 🎉
