from datetime import datetime
import json

import pika

sum_ms = 0
num_of_reqs = 0


def callback(ch, method, properties, body):
    global sum_ms
    global num_of_reqs

    msg = json.loads(body)
    now = datetime.timestamp(datetime.now())
    msg_timestamp = int(msg.get("server_ts"))

    sum_ms += now - msg_timestamp
    num_of_reqs += 1

    print(f"Add new event: {msg.get('event_id')}")


def rabbit_consumer():
    credentials = pika.PlainCredentials("guest", "guest")
    parameters = pika.ConnectionParameters("localhost", 5672, "/", credentials)

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    queues = ["click", "custom", "visit"]
    for queue in queues:
        channel.queue_declare(queue=queue, durable=True)
        channel.basic_consume(queue=queue, on_message_callback=callback, auto_ack=True)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        avg_delay = sum_ms / num_of_reqs if num_of_reqs else 0
        print(
            f"\nTotal requests: %.0f, avg read delay: %.3f ms\n"
            % (num_of_reqs, avg_delay)
        )


if __name__ == "__main__":
    rabbit_consumer()
