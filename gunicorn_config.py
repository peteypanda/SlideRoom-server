bind = "unix:/tmp/gunicorn.sock"  # Unix socket for Nginx
workers = 4  # Number of worker processes
worker_class = "sync"  # Worker class type
timeout = 120  # Worker timeout in seconds
keepalive = 5  # Keepalive timeout
errorlog = "error.log"  # Error log file
accesslog = "access.log"  # Access log file
loglevel = "info"  # Log level
