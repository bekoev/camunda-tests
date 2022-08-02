import asyncio
import json

import grpc.aio
from zeebe_grpc import gateway_pb2
from zeebe_grpc import gateway_pb2_grpc


class Task():
    def __init__(self, type, impl) -> None:
        self.type = type
        self.impl = impl


class Worker():
    def __init__(self, channel: grpc.aio.Channel) -> None:
        self._gateway = gateway_pb2_grpc.GatewayStub(channel)
        self._tasks = []

    def task(self, type):
        def task_wrapper(task_impl):
            self._tasks.append(Task(type, task_impl))
        return task_wrapper

    async def work(self):
        while True:
            for task in self._tasks:
                print(f'Looking for some "{task.type}" jobs...')
                activate_jobs_response = self._gateway.ActivateJobs(
                    gateway_pb2.ActivateJobsRequest(
                        type=task.type,
                        worker='Python worker',
                        timeout=60_000,
                        maxJobsToActivate=32,
                        requestTimeout=60_000,  # Enable long polling
                    )
                )
                async for response in activate_jobs_response:
                    # TODO: Improve async jobs being executed synchronously
                    for job in response.jobs:
                        try:
                            result = await task.impl(job)
                            await self._gateway.CompleteJob(
                                gateway_pb2.CompleteJobRequest(
                                    jobKey=job.key,
                                    variables=json.dumps(result)))
                            print('Job Completed')
                        except Exception as e:
                            await self._gateway.FailJob(gateway_pb2.FailJobRequest(jobKey=job.key))  # noqa
                            print(f'Job Failed {e}')


channel = grpc.aio.insecure_channel('localhost:26500')  # TODO: check shutdown  # noqa
worker = Worker(channel)


@worker.task(type='echo')
async def echo_job(job):
    print(f'Got a job with ID={job.elementId}')
    await asyncio.sleep(2)
    return {}


if __name__ == '__main__':
    # Workaround, https://github.com/camunda-community-hub/pyzeebe/issues/239
    loop = asyncio.get_event_loop()
    loop.run_until_complete(worker.work())
