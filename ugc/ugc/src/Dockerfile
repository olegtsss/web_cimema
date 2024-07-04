FROM python:3.11-slim

WORKDIR /opt/ugc

ENV PYTHONPATH "/opt/ugc"

EXPOSE 5000

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

ENTRYPOINT [ "gunicorn", "wsgi:app", "-c", "gunicorn.conf.py" ]
