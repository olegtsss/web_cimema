from enum import Enum

QUERY = '''
SELECT
   film_work.id,
   film_work.title,
   film_work.description,
   film_work.rating,
   film_work.type,
   film_work.created,
   film_work.modified,
   COALESCE (
       json_agg(
           DISTINCT jsonb_build_object(
               'person_role', person_film_work.role,
               'person_id', person.id,
               'person_name', person.full_name
           )
       ) FILTER (WHERE person.id is not null),
       '[]'
   ) as persons,
   COALESCE (
       json_agg(
           DISTINCT jsonb_build_object(
               'genre_id', genre.id,
               'genre_name', genre.name
           )
       ) FILTER (WHERE genre.id is not null),
       '[]'
   ) as genres
FROM content.film_work
LEFT JOIN content.person_film_work ON person_film_work.film_work_id = film_work.id
LEFT JOIN content.person ON person.id = person_film_work.person_id
LEFT JOIN content.genre_film_work ON genre_film_work.film_work_id = film_work.id
LEFT JOIN content.genre ON genre.id = genre_film_work.genre_id
WHERE film_work.modified > %s OR person.modified > %s OR genre.modified > %s
GROUP BY film_work.id
ORDER BY film_work.modified DESC
'''


class Messages(str, Enum):
    ELK_INDEX_CREATE = 'Индекс ELK создан: %s'
    CURRENT_STATE = 'Получена последняя дата синхронизации: %s'
    ELK_DOWNLOAD = 'Загружено в ELK: %s'
    ELK_SLEEP = 'Отдыхаем %s ceкунд...'
    ELK_SLEEP_OFFLINE = 'ELK не доступен'
    BACKOFF_MESSAGE = 'Перехвачена ошибка (ожидание %sс.): %s'
