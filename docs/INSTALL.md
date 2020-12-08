# Installation

This document describe how to set up Orchestration/Workflow Manager for OpenSDS project.

* In this document Workflow Manager used is [StackStorm](https://stackstorm.com/).
* A Docker instance of StackStorm will be created from the StackStorms [repository](https://github.com/StackStorm/st2-docker)
* A StackStorm Pack with OpenSDS specific workflows and actions will be mounted into it.
* A Docker instance of Orchestration Manager will be started.
* A limited set of Workflows/Actions are available in [Orchestration](https://github.com/opensds/orchestration/tree/master/contrib/st2/opensds) reposity for OpenSDS.
* An example usage of these Workflows is listed below.

#### Install OpenSDS

Installation steps for OpenSDS is listed in the WIKI page of [OpenSDS](https://github.com/opensds/opensds/wiki).
The recommended OpenSDS Local Cluster Installation may be followed for initial testing of Orchestration.


#### Install Orchestration 
* Clone [OpenSDS Orchestration](https://github.com/opensds/orchestration)  project and install the Orchestration manager
    ```sh
    $ git clone https://github.com/opensds/orchestration
    $ cd orchestration
    $ pip install -r requirements.txt
    $ python setup.py install
    ```
* Install StackStorm
	The stackstorm [docker installer](https://github.com/StackStorm/st2-docker) repo is cloned, build as below.
    ```sh
    $ git clone https://github.com/stackstorm/st2-docker
    $ cd st2-docker
    $ make env
    ```
* Start docker container using docker-compose, copy opensds pack and register opensds pack
    ```sh
    $ docker-compose up -d
    $ docker cp <orchestration project>/contrib/st2/opensds <st2 container id>:/opt/stackstorm/packs/
	$ docker-compose exec stackstorm /bin/bash
	# st2ctl reload --register-all
    ```
* Register virtual environment while installing opensds first time.
	```sh
	# st2 run packs.setup_virtualenv packs=opensds
	```
* Check status of StackStorm installation. It should list all services and PIDs as below.
	```sh
	# st2ctl status
    ##### st2 components status #####
    st2actionrunner PID: 96
    ...
    mistral-server PID: 340
    mistral.api PID: 335
	```
* Update [orchestration.conf](https://github.com/opensds/orchestration/blob/master/scripts/install.sh) file and Run [OpenSDS Orchestration](https://github.com/opensds/orchestration) Orchestration manager. (config file section 'workflow' needs to be updated for 'host' and 'password' of Stackstorm)
    ```sh
    $ cd <OpenSDS Orchestration Directory>
    $ python setup.py install
    $ ./orchestration/server.py <orchestration.conf file path>
    ```

#### Installer script
The file [install.sh](https://github.com/opensds/orchestration/install.sh) may be used for automated installation of StackStorm and Workflows.

```sh
$  ./install.sh
```
And, default paths for st2-docker or opensds pack may be modified as below, if needed.

```sh
$ ST2_DOCKER_PATH="/opt/opensds/orchestration" ST2_WORKFLOW_PATH="/opt/opensds/orchestration/contrib/st2" ./scripts/install.sh
```

#### Known issue
* Creation of virtual environment for opensds (command: st2 run packs.setup_virtualenv packs=opensds) fails with [Exception: Failed to install requirement "six>=1.9.0,<2.0": Collecting six<2.0,>=1.9.0]. This can be ignored for now.
* Sometimes during multiple installations DB gets corrupt and some StackStorms services may not be running  (Eg. mistral-server, mistral.api). Because of this condition orchestration workflows will not run.
  * To check this, go to StackStorm Installer folder and check st2ctl status as below.

    ```sh
    $ cd /opt/st2-installer-linux-amd64
    $ docker-compose exec stackstorm st2ctl status
    ##### st2 components status #####
    st2actionrunner PID: 99
    ...
    st2scheduler PID: 55
    mistral-server is not running.     -----------------------------> ERROR condition
    mistral.api is not running.        -----------------------------> ERROR condition
    ```
  * To Fix this issue, run commands below:

    ```sh
    $ cd /opt/st2-installer-linux-amd64
    $ docker-compose exec stackstorm st2ctl stop
    $ docker-compose stop postgres
    $ docker system prune --volumes
    $ docker-compose up -d postgres
    $ docker-compose exec stackstorm st2ctl start
    ...
    ##### st2 components status #####
    st2actionrunner PID: 956
    ...
    mistral-server PID: 1400
    mistral.api PID: 1522
    ```

#### Example usage
OpenSDS Orchestration Dashboard OR CURL may be used for testing

For the examples below OpenSDS is installed on VM and both StackStorm and Orchestration manager are running on Host. Please replace '<>' with respective values.

* Get token from StackStorm with username st2admin, and password as input arguments
    ```sh
    $ curl -X POST -k -u st2admin:'<password>' https://localhost/auth/v1/tokens
    ```
* Provision Volume Workflow using StackStorm with input arguments
    ```sh
    $ curl -k -X POST \
        https://localhost/api/v1/executions \
        -H  'content-type: application/json' \
        -H  'X-Auth-Token: <stackstorm token>' \
        -d '{"action": "opensds.provision-volume", "user": null, "parameters": {"i_paddr": "<ip>", "port": "50040", "size": 1, "tenant_id": "<id>", "name": "test000", "auth_token": "<opensds token>", "host_id": "<host_id>"}}'
    ```

* Create Volume using StackStorm Action with input arguments
    ```sh
    $ curl -k -X POST   \
    https://localhost/api/v1/executions   \
    -H  'content-type: application/json'   \
    -H  'X-Auth-Token: <stackstorm token>'   \
    -d '{"action": "opensds.create-volume", "user": nul, "parameters": {"ip_addr": "<ip>", "port": "50040", "size": 1, "tenant_id": "<id>", "name": "test001", "auth_token": "<opensds token>"}}'
    ```
