#!/usr/bin/env python
'''
u0421u043au0440u0438u043fu0442 u0434u043bu044f u0437u0430u043fu0443u0441u043au0430 RQ Worker, u043eu0431u0440u0430u0431u0430u0442u044bu0432u0430u044eu0449u0435u0433u043e u043eu0447u0435u0440u0435u0434u044c u043fu0440u0435u0434u0441u043au0430u0437u0430u043du0438u0439.
'''
# u0418u0441u043fu0440u0430u0432u043bu0435u043du043du044bu0439 u0438u043cu043fu043eu0440u0442 - u0431u0435u0437 Connection
from rq import Worker, Queue
import redis
from ..core.config import settings

def main():
    conn = redis.from_url(settings.REDIS_URL)
    # u0418u0441u043fu0440u0430u0432u043bu0435u043du043du044bu0439 u0441u043fu043eu0441u043eu0431 u0437u0430u043fu0443u0441u043au0430 u0432u043eu0440u043au0435u0440u0430
    worker = Worker(['predict_queue'], connection=conn)
    worker.work()

if __name__ == '__main__':
    main()
