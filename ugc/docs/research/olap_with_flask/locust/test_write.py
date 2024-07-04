from locust import HttpUser, task, between


class CustomUser(HttpUser):
    wait_time = between(0.05, 0.1)
    host = 'http://kafka.olegtsss.ru:5005'

    @task
    def create(self):
        self.client.get('/create/')

# locust -f test_write.py --users 1000
# http://localhost:8089/
