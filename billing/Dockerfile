FROM python:3.10

WORKDIR /app
COPY src/ /app/src/
RUN groupadd -r web \
    && useradd -d /app -r -g web web \
    && chown web:web -R /app
USER web
RUN pip3 install --upgrade pip \
    && pip3 install -r src/requirements.txt
WORKDIR /app/src
ENV PATH="/app/.local/bin/:${PATH}"
ENTRYPOINT ["/bin/sh", "-c", "python3 -m gunicorn main:app -c gunicorn.conf.py"]
EXPOSE 5001/tcp
