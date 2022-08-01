import asyncio
import grpc.aio
import json
from zeebe_grpc import gateway_pb2
from zeebe_grpc import gateway_pb2_grpc


async def run():
    async with grpc.aio.insecure_channel('localhost:26500') as channel:
        gateway = gateway_pb2_grpc.GatewayStub(channel)
        topologyResponse = await gateway.Topology(gateway_pb2.TopologyRequest())  # noqa
        print(f'Zeebe gateway topology response:\n{topologyResponse}')

        print('Looking for some "echo" jobs...')
        while True:
            activate_jobs_response = gateway.ActivateJobs(
                gateway_pb2.ActivateJobsRequest(
                    type="echo",
                    worker="Python worker",
                    timeout=60_000,
                    maxJobsToActivate=32,
                    requestTimeout=60_000,  # Enable long polling
                )
            )
            async for response in activate_jobs_response:
                for job in response.jobs:
                    try:
                        print(f'Got a job with ID={job.elementId}')
                        await gateway.CompleteJob(
                            gateway_pb2.CompleteJobRequest(
                                jobKey=job.key,
                                variables=json.dumps({})))
                        print("Job Completed")
                    except Exception as e:
                        await gateway.FailJob(gateway_pb2.FailJobRequest(jobKey=job.key))  # noqa
                        print(f"Job Failed {e}")


if __name__ == '__main__':
    asyncio.run(run())
