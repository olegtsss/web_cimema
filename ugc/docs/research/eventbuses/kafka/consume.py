from datetime import datetime

from confluent_kafka import Consumer, KafkaException


def kafka_consumer():
    sum_ms = 0
    num_of_reqs = 0

    bootstrap_servers = "localhost:9092,localhost:9093,localhost:9094"
    consumer = Consumer(
        {
            "bootstrap.servers": bootstrap_servers,
            "group.id": "echo-messages-to-stdout",
            "auto.offset.reset": "earliest",
        }
    )

    topics = ["click", "visit", "custom"]
    consumer.subscribe(topics)

    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaException._PARTITION_EOF:
                    continue
                else:
                    break

            now = datetime.timestamp(datetime.now()) * 1000
            _, msg_timestamp = msg.timestamp()

            sum_ms += now - msg_timestamp
            num_of_reqs += 1

            print(f"Add new event: {msg.key().decode()}")

    except KeyboardInterrupt:
        avg_delay = sum_ms / num_of_reqs if num_of_reqs else 0
        print(
            f"\nTotal requests: %.0f, avg read delay: %.3f ms\n"
            % (num_of_reqs, avg_delay)
        )
        consumer.close()


if __name__ == "__main__":
    kafka_consumer()
