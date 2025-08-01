#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""This module contains Google Dataproc links."""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any

import attr

from airflow.exceptions import AirflowProviderDeprecationWarning
from airflow.providers.google.cloud.links.base import BASE_LINK, BaseGoogleLink
from airflow.providers.google.version_compat import (
    AIRFLOW_V_3_0_PLUS,
    BaseOperator,
    BaseOperatorLink,
)

if TYPE_CHECKING:
    from airflow.models.taskinstancekey import TaskInstanceKey
    from airflow.utils.context import Context

if AIRFLOW_V_3_0_PLUS:
    from airflow.sdk.execution_time.xcom import XCom
else:
    from airflow.models.xcom import XCom  # type: ignore[no-redef]


def __getattr__(name: str) -> Any:
    # PEP-562: deprecate module-level variable
    if name == "DATAPROC_JOB_LOG_LINK":
        # TODO: remove DATAPROC_JOB_LOG_LINK alias in the next major release
        # For backward-compatibility, DATAPROC_JOB_LINK was DATAPROC_JOB_LOG_LINK.
        warnings.warn(
            (
                "DATAPROC_JOB_LOG_LINK has been deprecated and will be removed in the next MAJOR release."
                " Please use DATAPROC_JOB_LINK instead"
            ),
            AirflowProviderDeprecationWarning,
            stacklevel=2,
        )
        return DATAPROC_JOB_LINK
    raise AttributeError(f"module {__name__} has no attribute {name}")


DATAPROC_BASE_LINK = BASE_LINK + "/dataproc"
DATAPROC_JOB_LINK = DATAPROC_BASE_LINK + "/jobs/{job_id}?region={region}&project={project_id}"

DATAPROC_CLUSTER_LINK = (
    DATAPROC_BASE_LINK + "/clusters/{cluster_id}/monitoring?region={region}&project={project_id}"
)
DATAPROC_WORKFLOW_TEMPLATE_LINK = (
    DATAPROC_BASE_LINK + "/workflows/templates/{region}/{workflow_template_id}?project={project_id}"
)
DATAPROC_WORKFLOW_LINK = (
    DATAPROC_BASE_LINK + "/workflows/instances/{region}/{workflow_id}?project={project_id}"
)

DATAPROC_BATCH_LINK = DATAPROC_BASE_LINK + "/batches/{region}/{batch_id}/monitoring?project={project_id}"
DATAPROC_BATCHES_LINK = DATAPROC_BASE_LINK + "/batches?project={project_id}"
DATAPROC_JOB_LINK_DEPRECATED = DATAPROC_BASE_LINK + "/jobs/{resource}?region={region}&project={project_id}"
DATAPROC_CLUSTER_LINK_DEPRECATED = (
    DATAPROC_BASE_LINK + "/clusters/{resource}/monitoring?region={region}&project={project_id}"
)


@attr.s(auto_attribs=True)
class DataprocLink(BaseOperatorLink):
    """
    Helper class for constructing Dataproc resource link.

    .. warning::
       This link is pending to deprecate.
    """

    name = "Dataproc resource"
    key = "conf"

    @staticmethod
    def persist(
        context: Context,
        url: str,
        resource: str,
        region: str,
        project_id: str,
    ):
        context["task_instance"].xcom_push(
            key=DataprocLink.key,
            value={
                "region": region,
                "project_id": project_id,
                "url": url,
                "resource": resource,
            },
        )

    def get_link(
        self,
        operator: BaseOperator,
        *,
        ti_key: TaskInstanceKey,
    ) -> str:
        conf = XCom.get_value(key=self.key, ti_key=ti_key)
        return (
            conf["url"].format(
                region=conf["region"], project_id=conf["project_id"], resource=conf["resource"]
            )
            if conf
            else ""
        )

    def __attrs_post_init__(self):
        # This link is still used into the selected operators
        # - airflow.providers.google.cloud.operators.dataproc.DataprocJobBaseOperator
        # As soon as we remove reference to this link we might deprecate it by add warning message
        # with `stacklevel=3` below in this method.
        ...


@attr.s(auto_attribs=True)
class DataprocListLink(BaseOperatorLink):
    """
    Helper class for constructing list of Dataproc resources link.

    .. warning::
       This link is deprecated.
    """

    name = "Dataproc resources"
    key = "list_conf"

    @staticmethod
    def persist(
        context: Context,
        url: str,
        project_id: str,
    ):
        context["task_instance"].xcom_push(
            key=DataprocListLink.key,
            value={
                "project_id": project_id,
                "url": url,
            },
        )

    def get_link(
        self,
        operator: BaseOperator,
        *,
        ti_key: TaskInstanceKey,
    ) -> str:
        list_conf = XCom.get_value(key=self.key, ti_key=ti_key)
        return (
            list_conf["url"].format(
                project_id=list_conf["project_id"],
            )
            if list_conf
            else ""
        )

    def __attrs_post_init__(self):
        warnings.warn(
            "This DataprocListLink is deprecated.",
            AirflowProviderDeprecationWarning,
            stacklevel=3,
        )


class DataprocClusterLink(BaseGoogleLink):
    """Helper class for constructing Dataproc Cluster Link."""

    name = "Dataproc Cluster"
    key = "dataproc_cluster"
    format_str = DATAPROC_CLUSTER_LINK


class DataprocJobLink(BaseGoogleLink):
    """Helper class for constructing Dataproc Job Link."""

    name = "Dataproc Job"
    key = "dataproc_job"
    format_str = DATAPROC_JOB_LINK


class DataprocWorkflowLink(BaseGoogleLink):
    """Helper class for constructing Dataproc Workflow Link."""

    name = "Dataproc Workflow"
    key = "dataproc_workflow"
    format_str = DATAPROC_WORKFLOW_LINK


class DataprocWorkflowTemplateLink(BaseGoogleLink):
    """Helper class for constructing Dataproc Workflow Template Link."""

    name = "Dataproc Workflow Template"
    key = "dataproc_workflow_template"
    format_str = DATAPROC_WORKFLOW_TEMPLATE_LINK


class DataprocBatchLink(BaseGoogleLink):
    """Helper class for constructing Dataproc Batch Link."""

    name = "Dataproc Batch"
    key = "dataproc_batch"
    format_str = DATAPROC_BATCH_LINK


class DataprocBatchesListLink(BaseGoogleLink):
    """Helper class for constructing Dataproc Batches List Link."""

    name = "Dataproc Batches List"
    key = "dataproc_batches_list"
    format_str = DATAPROC_BATCHES_LINK
