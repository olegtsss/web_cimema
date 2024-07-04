### Тестирование eventbus'ов

1) Разверните UGC следуя README.md из корня проекта

2) Разверните требуемый кластер. Билды описаны в `/research/eventbuses/kafka/docker-compose.yml` и `/research/eventbuses/rabbit/docker-compose.yml`.

3) Для объединения нод rabbit'а в кластер потребуются дополнительные манипуляции в 2-ой и 3-ей нодах. Детали описаны в [документации](https://www.rabbitmq.com/docs/clustering#creating):

```bash
# on rabbit2
docker exec -it rabbit2 bash
rabbitmqctl stop_app
rabbitmqctl reset
rabbitmqctl join_cluster rabbit@rabbit1
rabbitmqctl start_app

# on rabbit3
docker exec -it rabbit3 bash
rabbitmqctl stop_app
rabbitmqctl reset
rabbitmqctl join_cluster rabbit@rabbit1
rabbitmqctl start_app

# on rabbit1 - check cluster
docker exec -it rabbit1 bash
rabbitmqctl cluster_status
```

4) Установите зависимости:

```bash
pip install -r research/eventbuses/requirements.txt
```

5) Запустите consume'ра кластера:

```bash
python3 research/eventbuses/kafka/consume.py

# или

python3 research/eventbuses/rabbit/consume.py
```

6) Запустите локуст. По умолчанию UGC работает с kafka. Для работы с rabbit необходимо передать в параметре запуска флаг `--eventbus=rabbit`. Если используете ui, то в кастомных полях перед запуском теста будет соответствующий choice-параметр:

```bash
# Запуск с UI
locust -f locustfile.py --processes -1 --users 20

# Запус без UI для Kafka
locust -f locustfile.py --headless --processes -1 --users 20 --run-time=5m

# Запуск без UI для Rabbit
locust -f locustfile.py --headless --processes -1 --users 20 --run-time=5m --eventbus=rabbit
```

7) После окончания замеров остановите consume'ра `ctr + c`, в stdout будет рассчитан результат среднего времени между поступлением событий в eventbus и их фактическим прочтением.
