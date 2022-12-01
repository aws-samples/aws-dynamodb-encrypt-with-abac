# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import boto3
import botocore.session
from aws_lambda_powertools import Logger

logger = Logger()

resource_access_role_arn = os.environ.get('RESOURCE_ACCESS_ROLE_ARN')

sts = boto3.client('sts')

class TenantAbacSession(object):
    def __init__(self, tenant_id: str) -> None:
        if not tenant_id:
            raise ValueError("tenant_id missing")

        self._tenant_id = tenant_id
        
        # Assume the ResourceAccessRole, and set the requested tenant_id
        # as a session tag.
        assume_role_response = sts.assume_role(
            RoleArn=resource_access_role_arn,
            RoleSessionName=f"demo-tenant-session-{self._tenant_id}",
            DurationSeconds=900,
            Tags=[{'Key': 'TenantID','Value': self._tenant_id}],
        )

        # Create a botocore session object with the credentials from the
        # assumed role.
        self._botocore_session = botocore.session.get_session()
        self._botocore_session.set_credentials(
            access_key=assume_role_response['Credentials']['AccessKeyId'],
            secret_key=assume_role_response['Credentials']['SecretAccessKey'],
            token=assume_role_response['Credentials']['SessionToken'],        
        )

        # Also create a matching boto3 session object
        self._boto3_session = boto3.Session(
            botocore_session=self._botocore_session
        )

    @property
    def tenant_id(self) -> str:
        return self._tenant_id

    @property
    def botocore_session(self) -> botocore.session:
        return self._botocore_session

    @property
    def boto3_session(self) -> boto3.Session:
        return self._boto3_session