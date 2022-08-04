import json
from dataclasses import dataclass
from typing import Callable

import grpc
from zeebe_grpc import gateway_pb2, gateway_pb2_grpc


@dataclass(frozen=True)
class Task():
    type: str
    impl: Callable


class WorkerSync():
    def __init__(self, channel: grpc.Channel) -> None:
        self._gateway = gateway_pb2_grpc.GatewayStub(channel)
        self._tasks = []
        self._topo_formatters = []

    def task(self, type: str):
        def task_wrapper(task_impl: Callable):
            self._tasks.append(Task(type, task_impl))
            return task_impl
        return task_wrapper

    def topo_handler(self, f: Callable):
        self._topo_formatters.append(f)
        return f

    def work(self) -> None:
        topology = self._gateway.Topology(gateway_pb2.TopologyRequest())
        for topo_formatter in self._topo_formatters:
            topo_formatter(topology)

        while True:
            for task in self._tasks:
                activate_jobs_response = self._gateway.ActivateJobs(
                    gateway_pb2.ActivateJobsRequest(
                        type=task.type,
                        worker='Python worker',
                        timeout=60_000,
                        maxJobsToActivate=32,
                        requestTimeout=60_000,  # Enable long polling
                    )
                )
                for response in activate_jobs_response:
                    for job in response.jobs:
                        try:
                            task.impl(job)
                            self._gateway.CompleteJob(
                                gateway_pb2.CompleteJobRequest(
                                    jobKey=job.key,
                                    variables=json.dumps({})))
                            print('Job Completed')
                        except Exception as e:
                            self._gateway.FailJob(
                                gateway_pb2.FailJobRequest(jobKey=job.key))
                            print(f'Job Failed {e}')


channel = grpc.insecure_channel('localhost:26500')  # TODO: check greaceful shutdown # noqa
worker = WorkerSync(channel)


@worker.topo_handler
def print_all(topology):
    print(f'Zeebe gateway topology response:\n{topology}')


@worker.task(type='echo')
def echo(job):
    print(f'Got a job with ID={job.elementId}')


if __name__ == '__main__':
    worker.work()
