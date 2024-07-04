# Настроить серверы конфигураций
docker exec -it mongocfg1 bash -c 'echo "rs.initiate({_id: \"mongors1conf\", configsvr: true, members: [{_id: 0, host: \"mongocfg1\"}, {_id: 1, host: \"mongocfg2\"}, {_id: 2, host: \"mongocfg3\"}]})" | mongosh'

# Cоберём набор реплик первого шарда
docker exec -it mongors1n1 bash -c 'echo "rs.initiate({_id: \"mongors1\", members: [{_id: 0, host: \"mongors1n1\"}, {_id: 1, host: \"mongors1n2\"}, {_id: 2, host: \"mongors1n3\"}]})" | mongosh'
# Познакомим шард с маршрутизаторами, добавив их в кластер
docker exec -it mongos1 bash -c 'echo "sh.addShard(\"mongors1/mongors1n1\")" | mongosh'

# Cоберём набор реплик второго шарда
docker exec -it mongors2n1 bash -c 'echo "rs.initiate({_id: \"mongors2\", members: [{_id: 0, host: \"mongors2n1\"}, {_id: 1, host: \"mongors2n2\"}, {_id: 2, host: \"mongors2n3\"}]})" | mongosh'
# Познакомим шард с маршрутизаторами, добавив их в кластер
docker exec -it mongos1 bash -c 'echo "sh.addShard(\"mongors2/mongors2n1\")" | mongosh'

# Создать базу, коллекцию и включить шардирование
docker exec -it mongors1n1 bash -c 'echo "use test" | mongosh'
docker exec -it mongos1 bash -c 'echo "sh.enableSharding(\"test\")" | mongosh'
docker exec -it mongos1 bash -c 'echo "db.createCollection(\"rating\")" | mongosh'
docker exec -it mongos1 bash -c 'echo "sh.shardCollection(\"test.rating\", {\"film_id\": \"hashed\"})" | mongosh'
