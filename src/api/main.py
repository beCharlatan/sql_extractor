from fastapi import FastAPI
from prometheus_client import make_asgi_app, Counter, Gauge
import time

# Create FastAPI app
app = FastAPI(title="Extract Parameter Agent API")

# Create Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Define metrics
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
request_latency = Gauge('http_request_duration_seconds', 'HTTP request latency in seconds', ['method', 'endpoint'])

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    request_count.labels(method='GET', endpoint='/health').inc()
    with request_latency.labels(method='GET', endpoint='/health').time():
        return {"status": "healthy"}

@app.get("/")
async def root():
    """Root endpoint"""
    request_count.labels(method='GET', endpoint='/').inc()
    with request_latency.labels(method='GET', endpoint='/').time():
        return {"message": "Extract Parameter Agent API is running"} 