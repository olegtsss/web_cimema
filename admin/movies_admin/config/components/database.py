if os.getenv('NEED_SQLITE', False) == 'True':  # noqa
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(  # noqa
                BASE_DIR, os.getenv('SQLITE_DB', 'sqlite.db')  # noqa
            )
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': os.environ.get(  # noqa
                'DB_ENGINE', 'django.db.backends.postgresql'
            ),
            'NAME': os.environ.get('POSTGRES_DB', 'postgre'),  # noqa
            'USER': os.environ.get('POSTGRES_USER', 'postgre'),  # noqa
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'postgre'),  # noqa
            'HOST': os.environ.get('DB_HOST', '127.0.0.1'),  # noqa
            'PORT': os.environ.get('DB_PORT', 5432),  # noqa
            'OPTIONS': {
                'options': '-c search_path=public,content'
            }
        }
    }
