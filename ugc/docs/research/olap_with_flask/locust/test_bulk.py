from locust import HttpUser, task, between


BULK_SIZE = 100

class CustomUser(HttpUser):
    wait_time = between(0.05, 0.1)
    host = 'http://kafka.olegtsss.ru:5003'

    @task
    def create(self):
        self.client.get(f'/bulk/{BULK_SIZE}/')

# locust -f test_bulk.py --users 1000
# http://localhost:8089/