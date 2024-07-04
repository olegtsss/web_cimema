FROM python:3.11-slim

WORKDIR /opt/test

ENV PYTHONPATH "/opt/test"

EXPOSE 5002

COPY . .
RUN pip install --upgrade pip && pip install -r requirements.txt

ENTRYPOINT [ "gunicorn", "--bind", "0.0.0.0:5002", "wsgi:app"]
