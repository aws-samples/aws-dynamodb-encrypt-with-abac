# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
from aws_lambda_powertools import Logger
from dynamodb_encryption_sdk.encrypted.resource import EncryptedResource
from dynamodb_encryption_sdk.material_providers.aws_kms import AwsKmsCryptographicMaterialsProvider
from typing import Dict
from TenantAbacSession import TenantAbacSession

logger = Logger()

demo_table_name = os.environ.get('DEMO_TABLE_NAME')
demo_key_id = os.environ.get('DEMO_KEY_ID')

class TenantDataStore(object):
    def __init__(self, tenant_session: TenantAbacSession) -> None:
        self._tenant_session = tenant_session
        
        self._kms_cmp = AwsKmsCryptographicMaterialsProvider(
            key_id=demo_key_id,
            botocore_session=self._tenant_session.botocore_session,
        )

        # The EncryptedResource helper client provides an boto3-compatible 
        # Table resource. A regular boto3 resource can be used in its place
        # to switch to unencrypted mode of operation.
        # 
        # Example for unencrypted usage:
        # self._resource = self._tenant_session.boto3_session.resource('dynamodb')

        self._resource = EncryptedResource(
            resource=self._tenant_session.boto3_session.resource('dynamodb'),
            materials_provider=self._kms_cmp,
        )
        self._table = self._resource.Table(demo_table_name)

    def retrieve(self) -> Dict:
        response = self._table.get_item(
            Key={
                'tenant_id': self._tenant_session.tenant_id,
            },
        )
        return response.get('Item', {})

    def store(self, data: Dict) -> Dict:
        item = {
            **data,
            'tenant_id': self._tenant_session.tenant_id,
        }
        response = self._table.put_item(Item=item)
        logger.info("response", extra={'response': response})
        return item
