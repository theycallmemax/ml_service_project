#!/usr/bin/env python
'''
Скрипт для запуска RQ Worker, обрабатывающего очередь предсказаний.
'''

from rq import Worker, Queue
import redis
from ..core.config import settings

def main():
    conn = redis.from_url(settings.REDIS_URL)
    worker = Worker(['predict_queue'], connection=conn)
    worker.work()

if __name__ == '__main__':
    main()