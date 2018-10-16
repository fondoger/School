# Usage: locust -f basic.py

from locust import HttpLocust, TaskSet, task

def status(l):
    l.client.get("/status?id=135")

def timeline(l):
    headers = {
        "Authorization": "Basic ZXlKaGJHY2lPaUpJVXpJMU5pSXNJbWxoZENJNk1UVXhOelF3T1RZM01pd2laWGh3SWpveE5UUTRPVFExTmpjeWZRLmV5SnBaQ0k2TVgwLmJfWVV0ZlNDNUNUeDVMS3BnSEdvZWxROFF4OW1Oc3Z3RXdSWEtJbFFaeHc6"
    }
    l.client.get("/status?type=timeline", headers=headers)



class UserTasks(TaskSet):
    tasks = [ timeline, status ]

    @task
    def update(self):
        self.client.get("/update?platform=android")


class WebsiteUser(HttpLocust):
    host = "http://47.93.240.135/api/v1"

    task_set = UserTasks

    min_wait = 5000
    max_wait = 10000


