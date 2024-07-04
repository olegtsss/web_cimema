FROM python:3.11-slim

WORKDIR /opt/etl

ENV PYTHONPATH "/opt/etl"

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

ENTRYPOINT [ "python3", "etl.py" ]
