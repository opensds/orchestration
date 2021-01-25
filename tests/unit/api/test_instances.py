# Copyright 2019 The OpenSDS Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import uuid
import random
from datetime import datetime
from mock import patch, Mock
from orchestration.connectionmanager.st2 import St2


def test_post_instance(client):
    type_mime = 'application/json'
    header = {'Content-Type': type_mime, 'Accept': type_mime,
              'X-Auth-Token': 'abcde'}
    # Using random number to generate random string.
    # Name should be unique and with py27 run, the DB has already a name
    # column inserted. Now with py3.x run it, will fail as DB has already
    # the values for name column.
    random.seed(datetime.now())
    name = "test" + str(random.randint(1, 101))
    data = {
        "service_id": "26ab0773-fc5a-4211-a8e9-8e61ff16fa42",
        "action": "opensds.migration-bucket",
        "name": name,
        "parameters": {
            "ip_addr": "1.2.3.4",
            "port": "8089",
            "tenant_id": "7fc5d",
            "userId": "648e3089",
            "name": "testmigration",
            "description": "Migration_test_orchestration",
            "destBackend": "hw-backend",
            "srcBucketName": "aws-orchestrate",
            "destBucketName": "hw-orchestrate"
        }
    }
    url = '/v1beta/xyz/orchestration/instances'
    response = client.post(url, data=json.dumps(data), headers=header)
    assert response.status_code == 400


def test_post_instance_empty_1(client):
    type_mime = 'application/json'
    header = {'Content-Type': type_mime, 'Accept': type_mime}
    data = {}
    url = '/v1beta/xyz/orchestration/instances'
    response = client.post(url, data=json.dumps(data), headers=header)
    assert response.json == 'Bad Request. Authentication Token is missing'
    assert response.status_code == 400


def test_post_instance_empty_2(client):
    type_mime = 'application/json'
    header = {'Content-Type': type_mime, 'Accept': type_mime,
              'X-Auth-Token': 'abcde'}
    data = {}
    url = '/v1beta//orchestration/instances'
    response = client.post(url, data=json.dumps(data), headers=header)
    assert response.status_code == 404


def test_post_instance_empty_3(client):
    type_mime = 'application/json'
    header = {'Content-Type': type_mime, 'Accept': type_mime,
              'X-Auth-Token': 'abcde'}
    data = {'service_id': 'abc'}
    url = '/v1beta/xyz/orchestration/instances'
    response = client.post(url, data=json.dumps(data), headers=header)
    assert response.status_code == 400


def simple_get_service_definition(context=None, id=''):
    return {}


def test_post_instance_valid(client):
    id = str(uuid.uuid4())
    type_mime = 'application/json'
    header = {'Content-Type': type_mime, 'Accept': type_mime,
              'X-Auth-Token': 'abcde'}
    data = {}
    random.seed(datetime.now())
    name = "test" + str(random.randint(101, 201))
    data["service_id"] = "26ab0773-fc5a-4211-a8e9-8e61ff16fa42"
    data["action"] = "opensds.migration-bucket"
    data["name"] = name
    data["parameters"] = {}
    data["description"] = "Hello"
    data["user_id"] = "abc"
    url = '/v1beta/xyz/orchestration/instances'
    resp_data = {}
    resp_data["status"] = 'succeeded'
    resp_data["parameters"] = {}
    auth_resp = "abc12345"
    resp_data['parameters']['auth_token'] = auth_resp
    resp_data["action"] = {}
    resp_data["action"]["ref"] = "opensds.migration-bucket"
    resp_data['id'] = id

    # Mock the execute_action of the Orchestration Manager
    St2.execute_action = Mock(return_value=(201, json.dumps(resp_data)))
    # Mock the db api call
    mock = Mock(return_value={})
    with patch('orchestration.api.instances.get_service_definition', mock):
        response = client.post(url, data=json.dumps(data), headers=header)
    assert response.status_code == 200


def test_list_instance(client, no_om_authenticate,
                       mock_exec_stats, mock_exec_output, mock_list_services):
    response = client.get('/v1beta/xyz/orchestration/instances')
    assert response.status_code == 200


def test_list_instance_wrong_url(client):
    response = client.get('/v1beta/xyz/orchestration/nstances')
    assert response.status_code == 404


def test_get_instance_by_id(client):
    id = str(uuid.uuid4())
    url = '/v1beta/xyz/orchestration/instances/' + id
    response = client.get(url)
    assert response.json == {}


def test_get_instance_1(client, no_om_authenticate, mock_exec_output,
                        mock_exec_stats):
    url = '/v1beta/xyz/orchestration/instances'
    service_data = {}
    service_data['name'] = 'foo'
    service_data['id'] = 'abcd1234'
    service_data['output'] = ''
    service_data['created_at'] = ''
    service_data['updated_at'] = ''
    service_data['tenant_id'] = 'xyz'
    service_data['user_id'] = 'John'
    service_data['status'] = 'success'
    service_data['description'] = 'Test'
    response = client.get(url)
    assert response.status_code == 200


# mock the return of any function
def mockreturn(self='', id='', name=''):
    return 200, []


def test_delete_instance(client, monkeypatch):
    id = str(uuid.uuid4())
    url = '/v1beta/xyz/orchestration/' + id
    response = client.delete(url)
    # This should return 404 error as the ID is not present
    assert response.status_code == 404


def test_put_instance(client, monkeypatch):
    id = str(uuid.uuid4())
    url = '/v1beta/xyz/orchestration/' + id
    type_mime = 'application/json'
    header = {'Content-Type': type_mime, 'Accept': type_mime}
    data = {}
    response = client.put(url, data=json.dumps(data), headers=header)
    # This should return 404 error as the ID is not present
    assert response.status_code == 404


def test_get_instance(client):
    response = client.get('/v1beta/xyz/orchestration/instances/a1bcd')
    assert response.status_code == 404
