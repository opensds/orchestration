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

from flask import jsonify
from flask import Blueprint
from orchestration.connectionmanager.Connector import connector
from flask import request
import json
from orchestration.db.api \
    import create_workflow, list_workflows

instance = Blueprint("instance", __name__)

# API to execute a service.
# For example, St2 execution of this API will require 'action'
# as one of the parameter. 'parameters' maybe required for the Actions
# St2 example of data:/v1beta/orchestration/instances -H
# "Content-Type:application/json" -d
# '{"action":"aks.ak_echo_py", "parameters":{"message":"Hello World"}}'
@instance.route("/v1beta/orchestration/instances", methods=['POST'])
def instance_ops():
    c = connector().morph()
    content = request.get_json()
    ret = c.execute_action(content)
    ret_json = json.loads(ret)
    wf_hash = {}
    wf_hash['id'] = ret_json['id']
    wf_hash['name'] = ret_json['action']['name']
    wf_hash['input'] = json.dumps(ret_json['parameters'])
    wf_hash['workflow_definition_id'] = ret_json['action']['ref']

    # Create the record of this instance in DB
    create_workflow(None, wf_hash)
    return jsonify(response=ret_json), 200


@instance.route("/v1beta/orchestration/instances/create", methods=['POST'])
def create_action():
    c = connector().morph()
    content = request.get_json()
    ret = c.create_action(content)
    return jsonify(response=json.dumps(ret)), 200


# Internal API to get the Workflow definitions
# This can be imported and called directly from
# outside
def get_wfds():
    c = connector().morph()
    ret = c.list_actions('opensds')
    return ret


@instance.route(
    "/v1beta/orchestration/workflows",
    methods=['GET'])
def wfds_ops():
    return jsonify(response=get_wfds()), 200


@instance.route(
    "/v1beta/orchestration/instances",
    methods=['GET', 'PUT', 'DELETE'])
def wf_ops():
    c = connector().morph()
    method = request.method
    if method == 'GET':
        ret = list_workflows(None)
        return jsonify(response=ret), 200
    elif method == 'PUT':
        content = request.get_json()
        ret = c.update_action(id, content)
        return jsonify(response=json.dumps(ret)), 200
    elif method == 'DELETE':
        content = request.get_json()
        ret = c.delete_action(id, content)
        return jsonify(response=json.dumps(ret)), 200
