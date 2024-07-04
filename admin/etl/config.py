import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    postgres_dsn: dict = {
        'dbname': os.getenv('POSTGRES_DB', 'postgres'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
        'host': os.getenv('DB_HOST_FOR_ELK', '127.0.0.1'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'options': '-c search_path=content'
    }

    elk_storage_file: str = 'storage.json'
    elk_dsn: str = (
        'http://'
        f'{os.getenv("ELK_HOST", "127.0.0.1")}:'
        f'{int(os.getenv("ELK_PORT", "9200"))}'
    )
    elk_index_name: str = 'movies'
    elk_index_settings: dict = {
        'refresh_interval': '1s',
        'analysis': {
            'filter': {
                'english_stop': {
                    'type': 'stop',
                    'stopwords': '_english_'
                },
                'english_stemmer': {
                    'type': 'stemmer',
                    'language': 'english'
                },
                'english_possessive_stemmer': {
                    'type': 'stemmer',
                    'language': 'possessive_english'
                },
                'russian_stop': {
                    'type': 'stop',
                    'stopwords': '_russian_'
                },
                'russian_stemmer': {
                    'type': 'stemmer',
                    'language': 'russian'
                }
            },
            'analyzer': {
                'ru_en': {
                    'tokenizer': 'standard',
                    'filter': [
                        'lowercase',
                        'english_stop',
                        'english_stemmer',
                        'english_possessive_stemmer',
                        'russian_stop',
                        'russian_stemmer'
                    ]
                }
            }
        }
    }
    elk_index_mapping: dict = {
        'dynamic': 'strict',
        'properties': {
            'id': {
                'type': 'keyword'
            },
            'imdb_rating': {
                'type': 'float'
            },
            'genre': {
                'type': 'keyword'
            },
            'genres': {
                'type': 'nested',
                'dynamic': 'strict',
                'properties': {
                    'id': {
                        'type': 'keyword'
                    },
                    'name': {
                        'type': 'text',
                        'analyzer': 'ru_en'
                    }
                }
            },
            'title': {
                'type': 'text',
                'analyzer': 'ru_en',
                'fields': {
                    'raw': {
                        'type': 'keyword'
                    }
                }
            },
            'description': {
                'type': 'text',
                'analyzer': 'ru_en'
            },
            'director': {
                'type': 'text',
                'analyzer': 'ru_en'
            },
            'directors': {
                'type': 'nested',
                'dynamic': 'strict',
                'properties': {
                    'id': {
                        'type': 'keyword'
                    },
                    'name': {
                        'type': 'text',
                        'analyzer': 'ru_en'
                    }
                }
            },
            'actors_names': {
                'type': 'text',
                'analyzer': 'ru_en'
            },
            'writers_names': {
                'type': 'text',
                'analyzer': 'ru_en'
            },
            'actors': {
                'type': 'nested',
                'dynamic': 'strict',
                'properties': {
                    'id': {
                        'type': 'keyword'
                    },
                    'name': {
                        'type': 'text',
                        'analyzer': 'ru_en'
                    }
                }
            },
            'writers': {
                'type': 'nested',
                'dynamic': 'strict',
                'properties': {
                    'id': {
                        'type': 'keyword'
                    },
                    'name': {
                        'type': 'text',
                        'analyzer': 'ru_en'
                    }
                }
            }
        }
    }

    batch_size: int = 300
    sleep_time: int = 10
    state_key: str = 'modified'

    class Config:
        env_file = './../.env'


app_settings = Settings()
