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
from orchestration.connectionmanager.connector import Connector
from flask import request
import json
from orchestration.db.api \
    import create_workflow, create_service, \
    get_sd_wfd_association, delete_service, get_wf_sd, \
    list_services, get_service, get_service_definition, \
    get_execid_instance, update_service, update_workflow
from orchestration.api.apiconstants import Apiconstants
from orchestration.utils.config import logger, config_file, \
    get_config

instance = Blueprint("instance", __name__)

status_map = {'requested': 'Running', 'succeeded': 'Success',
              'failed': 'Failed', 'running': 'Running',
              'scheduled': 'Running'
              }


# API to execute a service.
# For example, St2 execution of this API will require 'action'
# as one of the parameter. 'parameters' maybe required for the Actions
# St2 example of data:/v1beta/orchestration/instances -H
# "Content-Type:application/json" -d
# '{"action":"aks.ak_echo_py", "parameters":{"message":"Hello World"}}'
@instance.route("/v1beta/<string:tenant_id>/orchestration/instances",
                methods=['POST'])
def instance_ops(tenant_id=''):
    c = Connector().morph()
    content = request.get_json()
    AUTH_TOKEN = request.headers.get('X-Auth-Token')
    # TODO: Need to check, When orchestration APIs authentication
    # is implemented
    if AUTH_TOKEN == '' or AUTH_TOKEN is None:
        err_msg = 'Bad Request. Authentication Token is missing'
        return jsonify(err_msg), Apiconstants.HTTP_ERR_BAD_REQUEST
    if tenant_id == '':
        err_msg = 'bad URL. tenant id is empty'
        return jsonify(err_msg), Apiconstants.HTTP_ERR_NOTFOUND

    # get the service_definition id from the content and remove this from data
    try:
        sd_id = content['service_id']
        del content['service_id']
        if sd_id == '':
            raise ValueError('Empty service definition id')
        if get_service_definition(None, sd_id) is None:
            raise ValueError('Invalid service definition id')
    except Exception as e:
        err_msg = 'required input service_id is missing or incorrect'
        logger.error("%s. Exception [%s]" % (err_msg, str(e)))
        return jsonify(err_msg), Apiconstants.HTTP_ERR_BAD_REQUEST

    # Name should be provided by the instance creator
    try:
        service_name = content['name']
        del content['name']
        if service_name == '':
            raise ValueError('Empty service name')
    except Exception as e:
        err_msg = 'required input service \'name\' is missing'
        logger.error("%s. Exception [%s]" % (err_msg, str(e)))
        return jsonify(err_msg), Apiconstants.HTTP_ERR_BAD_REQUEST

    # Description of the instance getting created
    try:
        description = content['description']
        del content['description']
        if description == '':
            raise ValueError('Empty service description provided')
    except Exception as e:
        # If description is not provided, the instance creation should proceed
        logger.info("no instance description provided. Set empty %s", str(e))

    # user_id of the instance creator
    try:
        user_id = content['user_id']
        del content['user_id']
        if description == '':
            raise ValueError('Empty user id provided')
    except Exception as e:
        # If description is not provided, the instance creation should proceed
        logger.info("no user_id provided. Exception [%s]", str(e))

    # action of the instance creator
    try:
        action = content['action']
        if action == '':
            raise ValueError('Empty action provided')
        if action == 'opensds.provision-volume':
            content['parameters']['ip_addr'] = get_config(config_file,
                                                          'hotpot', 'host')
            content['parameters']['port'] = get_config(config_file,
                                                       'hotpot', 'port')
        else:
            content['parameters']['ip_addr'] = get_config(config_file,
                                                          'gelato', 'host')
            content['parameters']['port'] = get_config(config_file,
                                                       'gelato', 'port')
    except Exception as e:
        err_msg = 'required input action is missing'
        logger.error("%s. Exception [%s]" % (err_msg, str(e)))
        return jsonify(err_msg), Apiconstants.HTTP_ERR_BAD_REQUEST

    content['parameters']['tenant_id'] = tenant_id
    content['parameters']['auth_token'] = AUTH_TOKEN
    try:
        rc, ret = c.execute_action(content)
        if(rc != Apiconstants.HTTP_CREATED):
            logger.error("api response received return code[%d]", rc)
            return jsonify(json.loads(ret)), rc
    except Exception as ex:
        # The requests may throw ConnectionError. Handle it
        logger.error("recieved exception [%s] while executing action", str(ex))
        return jsonify([]), 500

    ret_json = json.loads(ret)

    # creat service attribs from the return
    service_map = {}
    service_map['name'] = service_name
    # Don't store auth_token
    del ret_json['parameters']['auth_token']
    service_map['input'] = json.dumps(ret_json['parameters'])
    # get the service definition id
    service_map['service_definition_id'] = sd_id
    service_map['description'] = description
    service_map['user_id'] = user_id
    service_map['tenant_id'] = tenant_id
    service_map['status'] = status_map[ret_json['status']]
    try:
        service_obj = create_service(None, service_map)
    except Exception as ex:
        err_msg = str(ex)
        logger.error("received exception in creating service: %s", err_msg)
        err_ret = {}
        err_ret['message'] = err_msg
        return jsonify(err_ret), Apiconstants.HTTP_ERR_BAD_REQUEST

    # Now that service is created append appropriate values
    service_map['service_id'] = sd_id
    service_map['id'] = service_obj['id']
    service_map['created_at'] = service_obj['created_at']
    service_map['updated_at'] = service_obj['updated_at']
    service_map['input'] = ret_json['parameters']

    wf_hash = {}
    wf_hash['id'] = ret_json['id']
    wf_hash['name'] = service_name
    wf_hash['description'] = description
    wf_hash['input'] = json.dumps(ret_json['parameters'])
    wf_hash['workflow_source'] = ret_json['action']['ref']
    wf_hash['service_id'] = service_obj['id']
    wf_hash['status'] = ret_json['status']

    wd_id = ''
    try:
        service_wf_list = get_sd_wfd_association(None, sd_id)
        if not service_wf_list or service_wf_list is None:
            logger.info("could not get workflow definition for sd %s", sd_id)
        else:
            for sd, wd in service_wf_list:
                wd_id = wd.id
    except Exception as e:
        logger.error("received exception while getting wfd id %s", str(e))

    wf_hash['workflow_definition_id'] = wd_id

    # Create the record of this instance in DB
    logger.info("creating workflow table with record [%s]", str(wf_hash))

    # Create a Service of this execution.
    create_workflow(None, wf_hash)
    return jsonify(service_map), 200


'''
Internal API to get the Workflow definitions
This can be imported and called directly from
outside
'''


def get_wfds():
    c = Connector().morph()
    ret = c.list_actions('opensds')
    logger.debug("returning list of actions: %s" % (ret))
    return ret


# This to get the Workflow definition from st2
def get_wfd(id):
    c = Connector().morph()
    rc, ret = c.get_action(id, 'opensds')
    if rc != Apiconstants.HTTP_OK:
        logger.error("api response return error code [%d]", rc)
        return None
    return ret


@instance.route(
    "/v1beta/orchestration/workflows",
    methods=['GET'])
def wfds_ops():
    ret = get_wfds()
    return jsonify(ret), 200


# Get all the instances of a particular service definition
@instance.route(
    "/v1beta/orchestration/instances/service/<string:service_def_id>",
    methods=['GET'])
def get_instance_sd(service_def_id=''):
    # Query the db and return result
    ret = ''
    try:
        ret = get_wf_sd(service_def_id)
    except Exception as ex:
        logger.error("error in getting result for sd [%s]", str(ex))
        return jsonify(ret), 400
    try:
        # Create a hash of Service Definition Id and the Wfs
        wf_list = []
        for wf, service in ret:
            # Create a hash of all the WFs
            wf_hash = {'name': service.name,
                       'input': json.loads(service.input),
                       'id': service.id,
                       'output': service.output,
                       'created_at':  service.created_at,
                       'updated_at':  service.updated_at,
                       'service_definition_id': service_def_id,
                       'tenant_id': service.tenant_id,
                       'user_id': service.user_id,
                       'status': service.status,
                       'description': service.description
                       }

            status, output = _update_status_and_output(wf.service_id)
            wf_hash['status'] = status
            wf_hash['output'] = output
            # Add the Wfs to the List
            wf_list.append(wf_hash)

    except Exception as ex:
        logger.error("error in getting the WFs for SD [%s]: \
            [%s]" % (service_def_id, str(ex)))
    return jsonify(wf_list), 200


@instance.route(
    "/v1beta/<string:tenant_id>/orchestration/instances/<string:instance_id>",
    methods=['GET', 'PUT', 'DELETE'])
@instance.route(
    "/v1beta/<string:tenant_id>/orchestration/instances",
    methods=['GET'])
def wf_ops(tenant_id='', instance_id=''):
    c = Connector().morph()
    method = request.method
    global ret
    if method == 'GET':
        logger.info("inside getting actions")
        if instance_id == '':
            try:
                service_def_id = request.args.get('service_def')
                if service_def_id is not None:
                    return get_instance_sd(service_def_id)
            except Exception as e:
                logger.debug("no service_def query params passed.[%s]", str(e))
            ret = list_services(None)
            for service in ret:
                service['input'] = json.loads(service['input'])
                status, output = _update_status_and_output(service['id'])
                service['status'] = status
                service['output'] = output
                service['service_id'] = service['service_definition_id']
                del service['service_definition_id']
        else:
            try:
                ret = get_service(None, instance_id)
                ret['input'] = json.loads(ret['input'])
            except Exception as e:
                logger.error("error in getting service for [%s]: [%s]",
                             instance_id, str(e))
                return jsonify({}), 404
            status, output = _update_status_and_output(instance_id)
            ret['status'] = status
            ret['output'] = output
            ret['service_id'] = ret['service_definition_id']
            del ret['service_definition_id']

        logger.debug("returning list of workflows: %s" % (ret))
        return jsonify(ret), 200
    elif method == 'PUT':
        content = request.get_json()
        content['parameters']['tenant_id'] = tenant_id
        rc, ret = c.update_action(id, content)
        if(rc != Apiconstants.HTTP_OK):
            return jsonify(json.loads(ret)), rc

        return jsonify(json.dumps(ret)), 200
    elif method == 'DELETE':
        rc, ret = Apiconstants.HTTP_OK, 'Success'
        try:
            ret_instance = get_service(None, instance_id)
            if ret_instance is None:
                raise ValueError("Instance id is not present")
            else:
                logger.info("deleting instance %s", instance_id)
                delete_service(None, instance_id)
        except Exception as e:
            logger.error("error while deleting instance from db. [%s]", str(e))
            rc, ret = Apiconstants.HTTP_ERR_NOTFOUND, 'Failed'
        return jsonify(ret), rc


# For an instance get the latest status and output and update
def _update_status_and_output(instance_id=''):
    c = Connector().morph()
    global exec_id
    try:
        exec_id = get_execid_instance(None, instance_id)
    except Exception as e:
        logger.error("error in getting wf ID for [%s]:[%s]",
                     instance_id, str(e))
        return '', ''
    update_hash = {}

    rc, ret = c.get_execution_stats(exec_id)
    if rc != Apiconstants.HTTP_OK:
        logger.error("error in getting the execution stat for %s", instance_id)
    else:
        ret_json = json.loads(ret)
        if 'status' in ret_json:
            status = status_map[ret_json['status']]
            update_hash['status'] = status

    rc, ret = c.get_execution_output(exec_id)
    if rc != Apiconstants.HTTP_OK:
        logger.error("error in getting the execution o/p for %s", instance_id)
    else:
        output = ret
        update_hash['output'] = output
    update_service(None, instance_id, update_hash)
    update_workflow(None, exec_id, update_hash)
    return status, output
