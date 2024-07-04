bind = "0.0.0.0:5000"
worker_class = "uvicorn.workers.UvicornWorker"
workers = 1
accesslog = "logs/gunicorn/access.log"
loglevel = "INFO"
