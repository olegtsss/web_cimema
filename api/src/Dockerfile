FROM python:3.11-slim

WORKDIR /opt/practix

ENV PYTHONPATH "/opt/practix"

EXPOSE 5000

RUN mkdir -p logs/gunicorn/ && touch -a logs/gunicorn/access.log

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

ENTRYPOINT [ "gunicorn", "main:app", "-c", "gunicorn.conf.py" ]
