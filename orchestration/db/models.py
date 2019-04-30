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
import uuid
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, ForeignKey
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.orm import relationship

Base = declarative_base()


class ModelBase(Base):
    __abstract__ = True
    id = Column(String(36),  default=lambda: str(
        uuid.uuid4()), primary_key=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


definition_association = Table('service_workflow_definition_associations',
                               Base.metadata,
                               Column('service_definition_id', String,
                                      ForeignKey('service_definitions.id')),
                               Column('workflow_definition_id', String,
                                      ForeignKey('workflow_definitions.id')))


class ServiceDefinition(ModelBase):
    """Declares service template model"""
    __tablename__ = 'service_definitions'
    tenant_id = Column(String(255))
    user_id = Column(String(255))
    name = Column(String(255))
    description = Column(String)
    input = Column(Text)
    constraint = Column(Text)
    workflow_definitions = relationship(
        "WorkflowDefinition",
        secondary=definition_association)


class WorkflowDefinition(ModelBase):
    """Declares workflow template model"""
    __tablename__ = "workflow_definitions"
    name = Column(String(255))
    description = Column(String)
    definition = Column(Text)
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
