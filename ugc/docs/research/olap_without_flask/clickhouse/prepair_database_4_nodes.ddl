# Создание дистрибутивной таблицы


# docker exec -it clickhouse-node1 bash
# clickhouse-client
CREATE DATABASE benchmarks;
CREATE TABLE benchmarks.test
    (id UUID, user_id UUID, film_id UUID, rating Int8)
    Engine=ReplicatedMergeTree('/clickhouse/tables/benchmarks1/test', 'replica_1')
    PARTITION BY sipHash64(rating) % 16
    ORDER BY tuple();


# docker exec -it clickhouse-node2 bash
# clickhouse-client
CREATE DATABASE benchmarks;
CREATE TABLE benchmarks.test
    (id UUID, user_id UUID, film_id UUID, rating Int8)
    Engine=ReplicatedMergeTree('/clickhouse/tables/benchmarks2/test', 'replica_2')
    PARTITION BY sipHash64(rating) % 16
    ORDER BY tuple();


# docker exec -it clickhouse-node3 bash
# clickhouse-client
CREATE DATABASE benchmarks;
CREATE TABLE benchmarks.test
    (id UUID, user_id UUID, film_id UUID, rating Int8)
    Engine=ReplicatedMergeTree('/clickhouse/tables/benchmarks3/test', 'replica_3')
    PARTITION BY sipHash64(rating) % 16
    ORDER BY tuple();


# docker exec -it clickhouse-node4 bash
# clickhouse-client
CREATE DATABASE benchmarks;
CREATE TABLE benchmarks.test
    (id UUID, user_id UUID, film_id UUID, rating Int8)
    Engine=ReplicatedMergeTree('/clickhouse/tables/benchmarks4/test', 'replica_4')
    PARTITION BY sipHash64(rating) % 16
    ORDER BY tuple();
