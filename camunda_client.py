import asyncio
from typing import Dict

from pyzeebe import Job
from pyzeebe import ZeebeWorker
from pyzeebe import create_insecure_channel


grpc_channel = create_insecure_channel(hostname='localhost', port=26500)
worker = ZeebeWorker(grpc_channel)


async def print_job_id(job: Job) -> Job:
    print(f'Got a job with ID={job.element_id}')
    return job


async def print_completed(job: Job) -> Job:
    print(f'Job Completed')
    return job


@worker.task(task_type='echo', before=[print_job_id], after=[print_completed])
async def example_task() -> Dict:
    await asyncio.sleep(2)
    return {}


if __name__ == '__main__':
    # Workaround from https://github.com/camunda-community-hub/pyzeebe/issues/239
    loop = asyncio.get_event_loop()
    loop.run_until_complete(worker.work())
