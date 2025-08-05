# Gunicorn configuration for Render.com
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '10000')}"

# Worker processes
workers = 1
worker_class = "uvicorn.workers.UvicornWorker"

# Application
module = "app.main:app"

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Timeout
timeout = 120
keepalive = 2

# Process naming
proc_name = "twsignals-webhook"

# Preload app
preload_app = True