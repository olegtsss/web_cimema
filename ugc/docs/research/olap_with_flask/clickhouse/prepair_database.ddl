# Создание дистрибутивной реплицированной таблицы


# docker exec -it clickhouse-node1 bash
# clickhouse-client
CREATE DATABASE benchmarks;
CREATE TABLE benchmarks.test
    (
        id UUID, event_id UUID, request_id UUID, session_id UUID, user_id UUID,
        event_time DateTime, user_ts Int64, server_ts Int64, eventbus_ts Int64,
        url String, event_type String, event_subtype String, payload Map(String, String)
    )
    Engine=ReplicatedMergeTree('/clickhouse/tables/benchmarks1/test', 'replica_1')
    PARTITION BY toYYYYMMDD(event_time)
    ORDER BY id;
CREATE TABLE default.test
    (
        id UUID, event_id UUID, request_id UUID, session_id UUID, user_id UUID,
        event_time DateTime, user_ts Int64, server_ts Int64, eventbus_ts Int64,
        url String, event_type String, event_subtype String, payload Map(String, String)
    )
    ENGINE = Distributed('company_cluster', '', test, rand());

# docker exec -it clickhouse-node2 bash
# clickhouse-client
CREATE DATABASE replica;
CREATE TABLE replica.test
    (
        id UUID, event_id UUID, request_id UUID, session_id UUID, user_id UUID,
        event_time DateTime, user_ts Int64, server_ts Int64, eventbus_ts Int64,
        url String, event_type String, event_subtype String, payload Map(String, String)
    )
    Engine=ReplicatedMergeTree('/clickhouse/tables/benchmarks1/test', 'replica_2')
    PARTITION BY toYYYYMMDD(event_time)
    ORDER BY id;

# docker exec -it clickhouse-node3 bash
# clickhouse-client
CREATE DATABASE benchmarks;
CREATE TABLE benchmarks.test
    (
        id UUID, event_id UUID, request_id UUID, session_id UUID, user_id UUID,
        event_time DateTime, user_ts Int64, server_ts Int64, eventbus_ts Int64,
        url String, event_type String, event_subtype String, payload Map(String, String)
    )
    Engine=ReplicatedMergeTree('/clickhouse/tables/benchmarks2/test', 'replica_1')
    PARTITION BY toYYYYMMDD(event_time)
    ORDER BY id;
CREATE TABLE default.test
    (
        id UUID, event_id UUID, request_id UUID, session_id UUID, user_id UUID,
        event_time DateTime, user_ts Int64, server_ts Int64, eventbus_ts Int64,
        url String, event_type String, event_subtype String, payload Map(String, String)
    )
    ENGINE = Distributed('company_cluster', '', test, rand());

# docker exec -it clickhouse-node4 bash
# clickhouse-client
CREATE DATABASE replica;
CREATE TABLE replica.test
    (
        id UUID, event_id UUID, request_id UUID, session_id UUID, user_id UUID,
        event_time DateTime, user_ts Int64, server_ts Int64, eventbus_ts Int64,
        url String, event_type String, event_subtype String, payload Map(String, String)
    )
    Engine=ReplicatedMergeTree('/clickhouse/tables/benchmarks2/test', 'replica_2')
    PARTITION BY toYYYYMMDD(event_time)
    ORDER BY id;
