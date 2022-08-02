# camunda-tests
This repo contains test code in Python around the https://camunda.com/ system.

## Preparing a local environment

### Run Zeebe
As per <https://docs.camunda.io/docs/self-managed/platform-deployment/docker/>:
```
docker run --name zeebe -p 26500-26502:26500-26502 camunda/zeebe:8.0.4
```

Note: use `camunda/zeebe:8.0.4` instead of `camunda/zeebe:latest` to keep consistency with Python code (see zeebe-grpc in `requirements.txt`).

### Install Camunda Desktop Modeler
As per <https://docs.camunda.io/docs/components/modeler/desktop-modeler/install-the-modeler/>.

### Setup Python environment
1. Optionally, create a Python virtual environment (e.g. `python3.10 -m venv venv`) and activate it (e.g. `source venv/bin/activate`).
1. `pip install -r requirements.txt`

## Running tests

### 101 A job worker-to-Zeebe handshake
1. Start the local Camunda Modeler, create a new BPMN diagram (of the Camunda Platform 8 version).
    1. Ensure or add: a start event -> a service task -> an end event.
    1. Add to the service task the type `echo`.
1. From Modeler, deploy the diagram to the local endpoint (should look like `localhost:26500`).
1. From Modeler, start the diagram.
1. In a terminal, execute `python camunda_client.py`
    * Note in the output something similar to:

        ```
        Looking for some "echo" jobs...
        Got a job with ID=Activity_10jeepw
        Job Completed
        ```
1. From Modeler, start the diagram again and note another "Got a job ... Job Completed" pair in the terminal.
1. In the terminal window, interrupt the execution (`^C`).
1. Test passed.

## References
* Zeebe API (gRPC) protobuf (note Zeebe version): https://raw.githubusercontent.com/camunda/zeebe/8.0.4/gateway-protocol/src/main/proto/gateway.proto