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

"""
Data access module.
"""

import uuid
from contextlib import contextmanager
from orchestration.db import Session
from orchestration.db import models
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import and_
from orchestration.utils.config import logger


# session_scope can be used cleanly in transaction,
# references the officel document of sqlalchemy.
@contextmanager
def session_scope():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as ex:
        session.rollback()
        raise ex
    finally:
        session.close()


def list_sd_wfd_associations(context, **filters):
    with session_scope() as session:
        query = session.query(models.ServiceDefinition,
                              models.WorkflowDefinition) \
            .filter(models.DefinitionAssociation.service_definition_id
                    == models.ServiceDefinition.id,
                    models.DefinitionAssociation.workflow_definition_id
                    == models.WorkflowDefinition.id) \
            .order_by(models.DefinitionAssociation.workflow_definition_id)
    if not query:
        return []
    else:
        return query.all()


def get_sd_wfd_association(context=None, id=''):
    # TODO: This function should return only a specific WFD not list
    with session_scope() as session:
        if id == '':
            return list_sd_wfd_associations(None)
        else:
            query = session.query(models.ServiceDefinition,
                                  models.WorkflowDefinition) \
                .filter(models.DefinitionAssociation.service_definition_id
                        == models.ServiceDefinition.id,
                        models.DefinitionAssociation.workflow_definition_id
                        == models.WorkflowDefinition.id) \
                .filter(models.ServiceDefinition.id == id) \
                .order_by(models.DefinitionAssociation.workflow_definition_id)
    if not query:
        return None
    else:
        return query.all()


# -------------------------data access for service definition------------------
def create_service_definition(context, values, workflow_definitions):
    try:
        if not values.get('id'):
            values['id'] = str(uuid.uuid4())

        service_definition = models.ServiceDefinition()
        service_definition.update(values)
        for workflow_definition in workflow_definitions:
            service_definition.workflow_definitions.append(workflow_definition)

        with session_scope() as session:
            session.add(service_definition)
    except RuntimeError:
        return None

    return get_service_definition(context, id=values['id'])


def get_service_definition(context=None, id=''):
    with session_scope() as session:
        if id == '':
            query = session.query(models.ServiceDefinition)
        else:
            query = session.query(models.ServiceDefinition).filter(
                models.ServiceDefinition.id == id)
    if not query or query.first() is None:
        return None
    else:
        return query.first().to_dict()


def list_service_definitions(context, **filters):
    func_name = 'list_service_definitions'
    logger.info("%s: Getting service definition for %s" % (func_name, id))
    try:
        with session_scope() as session:
            query = session.query(models.ServiceDefinition)
        if not query:
            return []
        else:
            return get_query_res(query.all(), models.ServiceDefinition)
    except SQLAlchemyError as sqe:
        logger.error("Received exception while listing service definition"
                     "[%s]", str(sqe))
        return []


def update_service_definition(context, values):
    pass


# -------------------------data access for service ----------------------------
def create_service(context, values):
    service = models.Service()
    if 'id' not in values:
        values['id'] = str(uuid.uuid4())

    for key, value in values.items():
        if hasattr(service, key):
            setattr(service, key, value)
    try:
        with session_scope() as session:
            session.add(service)
        return get_service(None, values['id'])
    except IntegrityError as ie:
        session.rollback()
        err_msg = str(ie)
        if err_msg.find('services.name'):
            err_msg = "Instance Name should be unique"
            raise ValueError(err_msg)
    except SQLAlchemyError as sqe:
        raise ValueError(str(sqe))


def get_service(context, id):
    try:
        with session_scope() as session:
            query = session.query(models.Service).filter(
                models.Service.id == id)
        return None if not query else query.first().to_dict()
    except Exception as e:
        logger.error("exception while getting the service %s: [%s]", str(e))
        return None


def list_services(context, **filters):
    with session_scope() as session:
        query = session.query(models.Service)
    return [] if not query else get_query_res(query.all(), models.Service)


def update_service(context, id, values):
    try:
        with session_scope() as session:
            session.query(models.Service).filter(
                models.Service.id == id).update(
                values, synchronize_session=False)
    except Exception as e:
        logger.error("error updating the service: %s", str(e))


def delete_service(context, id):
    with session_scope() as session:
        session.query(models.Service).filter(
            models.Service.id == id).delete()


def delete_service_definition(context, id):
    with session_scope() as session:
        session.query(models.ServiceDefinition).filter(
            models.ServiceDefinition.id == id).delete()


# ------------------------data access for workflow definition-----------------
def create_workflow_definition(context, values):
    try:
        workflow_definition = models.WorkflowDefinition()
        for key, value in values.items():
            if hasattr(workflow_definition, key):
                setattr(workflow_definition, key, value)

        if not workflow_definition.id:
            workflow_definition.id = str(uuid.uuid4())
        with session_scope() as session:
            session.add(workflow_definition)
    except RuntimeError:
        return None
    return workflow_definition


def get_workflow_definition(context, id, wfe_type):
    with session_scope() as session:
        if id == '':
            query = session.query(models.WorkflowDefinition)
        else:
            query = session.query(models.WorkflowDefinition)\
                .filter(models.WorkflowDefinition.definition_source == id)\
                .filter(models.WorkflowDefinition.wfe_type == wfe_type)
    return None if not query else query.first()


def list_workflow_definitions(context, **filters):
    with session_scope() as session:
        query = session.query(models.WorkflowDefinition)
    if not query:
        return []
    else:
        return get_query_res(query.all(), models.WorkflowDefinition)


def update_workflow_definition():
    pass


def delete_workflow_definition():
    pass


# ------------------------data access for workflow --------------------------
def create_workflow(context, values):
    workflow = models.Workflow()
    for key, value in values.items():
        if hasattr(workflow, key):
            setattr(workflow, key, value)

    if not workflow.id:
        workflow.id = uuid.uuid4()
    with session_scope() as session:
        session.add(workflow)
    return workflow


def get_workflow(context, id):
    with session_scope() as session:
        query = session.query(models.Workflow).filter(
            models.Workflow.id == id)
    return None if not query else get_query_res(query.first(), models.Workflow)


def list_workflows(context, **filters):
    with session_scope() as session:
        query = session.query(models.Workflow)
    return [] if not query else get_query_res(query.all(), models.Workflow)


def update_workflow(context, id, values):
    try:
        with session_scope() as session:
            session.query(models.Workflow).filter(
                            models.Workflow.id == id).update(
                            values, synchronize_session=False)
    except Exception as e:
        logger.error("error in updating workflow for id [%s]:[%s]", id, str(e))


def get_wf_wfds(context, wfdid):
    try:
        with session_scope() as session:
            query = session.query(models.Workflow).filter(
                models.Workflow.workflow_definition_id == wfdid)
        return [] if not query else get_query_res(query.all(), models.Workflow)
    except SQLAlchemyError as sqe:
        logger.error("Received exception while listing workflows for [%s]:"
                     "[%s]" % (wfdid, str(sqe)))
        return []


# get the workflow id of a instance
def get_execid_instance(context, sid):
    try:
        with session_scope() as session:
            query = session.query(models.Workflow).filter(
                models.Workflow.service_id == sid)
            res = query.first().to_dict()
            return res['id']
    except SQLAlchemyError as sqe:
        logger.error("error in getting workflow id for %s:%s", sid, str(sqe))
        return ''


# Get all instances for a service definition id
def get_wf_sd(service_def_id):
    with session_scope() as session:

        query = session.query(models.Workflow, models.Service) \
            .join(models.Service, and_(
                models.Workflow.service_id == models.Service.id)).filter(
                models.Service.service_definition_id == service_def_id)

    return [] if not query else query.all()


def delete_workflow():
    pass


# ------------------------data access for task -------------------------------
def create_task(context, values):
    task = models.Task()
    for key, value in values.items():
        if hasattr(task, key):
            setattr(task, key, value)

    if not task.id:
        task.id = uuid.uuid4()

    with session_scope() as session:
        session.add(task)
    return task


def get_task(context, id):
    with session_scope() as session:
        query = session.query(models.Task).filter(models.Task.id == id)
    return None if not query else query.first()


def list_tasks(context, **filters):
    with session_scope() as session:
        query = session.query(models.Task)
    return [] if not query else query.all()


def update_task():
    pass


def delete_task():
    pass


# This fucntion takes the query result as obj
# and the tablename of the object.
# Returns the list of all the objects converted to dict
def get_query_res(obj, tablename):
    res_list = []
    # If the object is empty, return empty list
    if obj is None:
        return res_list
    # If the object is a single element
    if not isinstance(obj, list):
        row_hash = {}
        for c in tablename.__table__.columns.keys():
            row_hash[str(c)] = getattr(obj, c)
        return row_hash

    # if the object is list, o/p of query.list()
    for obj_elem in obj:
        row_hash = {}
        for c in tablename.__table__.columns.keys():
            row_hash[str(c)] = getattr(obj_elem, c)
        res_list.append(row_hash)
    return res_list
