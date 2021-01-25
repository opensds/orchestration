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
SQLAlchemy models for orchestration.
"""
import datetime
import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.inspection import inspect
from sqlalchemy.ext.declarative import as_declarative


@as_declarative()
class Base(object):
    """
    Class Base as a super class of models will provides some common functions
    for models.
    """

    def to_dict(self):
        return {c.key: getattr(self, c.key)
                for c in inspect(self).mapper.column_attrs}

    def update(self, values):
        for key, value in values.items():
            setattr(self, key, value)


class ModelBase(Base):
    __abstract__ = True
    id = Column(String(36),  default=lambda: str(
        uuid.uuid4()), primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow())
    updated_at = Column(DateTime, default=datetime.datetime.utcnow())


class DefinitionAssociation(Base):
    __tablename__ = 'service_workflow_definition_associations'
    service_definition_id = Column(
        String,
        ForeignKey('service_definitions.id'),
        primary_key=True)

    workflow_definition_id = Column(
        String,
        ForeignKey('workflow_definitions.id'),
        primary_key=True)


class ServiceDefinition(ModelBase):
    """Declares service template model"""
    __tablename__ = 'service_definitions'
    tenant_id = Column(String(255))
    user_id = Column(String(255))
    name = Column(String(255))
    description = Column(String)
    input = Column(Text)
    constraint = Column(Text)
    group = Column(String(255))
    workflow_definitions = relationship(
        "WorkflowDefinition",
        secondary='service_workflow_definition_associations')


class WorkflowDefinition(ModelBase):
    """Declares workflow template model"""
    __tablename__ = "workflow_definitions"
    name = Column(String(255))
    description = Column(String)
    definition = Column(Text)
    wfe_type = Column(String(255))
    definition_source = Column(String(255))


class Service(ModelBase):
    """Declares service metadata"""
    __tablename__ = "services"
    tenant_id = Column(String(255))
    user_id = Column(String(255))
    name = Column(String(255))
    description = Column(String)
    input = Column(Text)
    output = Column(Text)
    status = Column(String(255))
    service_definition_id = Column(String(36), index=True)
    service_definition = relationship(ServiceDefinition,
                                      backref="services",
                                      foreign_keys=service_definition_id,
                                      primaryjoin='Service. \
                                      service_definition_id == \
                                      ServiceDefinition.id')
    __table_args__ = (UniqueConstraint('name'),)


class Workflow(ModelBase):
    """Declares workflow metadata"""
    __tablename__ = "workflows"
    name = Column(String(255))
    description = Column(String)
    workflow_source = Column(String(255))
    input = Column(Text)
    output = Column(Text)
    status = Column(String(255))
    service_id = Column(String(36), index=True)
    service = relationship(Service,
                           backref="workflows",
                           foreign_keys=service_id,
                           primaryjoin='Workflow.service_id \
                                        == Service.id')
    workflow_definition_id = Column(String(36), index=True)
    workflow_definition = relationship(WorkflowDefinition, backref="workflows",
                                       foreign_keys=workflow_definition_id,
                                       primaryjoin='Workflow. \
                                       workflow_definition_id == \
                                       WorkflowDefinition.id')


class Task(ModelBase):
    """Declares task metadata"""
    __tablename__ = "tasks"
    name = Column(String(255))
    description = Column(String)
    task_source = Column(String(255))
    input = Column(Text)
    output = Column(Text)
    status = Column(String(255))
    workflow_id = Column(String(36), index=True)
    workflow = relationship(Workflow,
                            backref="tasks",
                            foreign_keys=workflow_id,
                            primaryjoin='Task.workflow_id == Workflow.id')
