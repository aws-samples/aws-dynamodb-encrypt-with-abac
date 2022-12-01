# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.exceptions import BadRequestError
from TenantAbacSession import TenantAbacSession
from TenantDataStore import TenantDataStore

# For sake of simplicity, this demo application is built as a monolithic
# function. Lambda Powertools are utilized for easy routing of API requests
# to the correct code paths.
#
# For production use, consider if your solution would benefit from further
# separation of concerns. A possible approach could be to separate the
# ResourceAccessRole assumption to a Lambda authorizer, and pass the assumed
# credentials to the downstream application function.

logger = Logger()
app = APIGatewayRestResolver()

# Note: This application does not perform authentication or authorization of
# api requests. The tenant_id from the request url is passed directly as the
# identity of the user to the TenantAbacSession class.
#
# In your own applications, make sure to acquire the tenant identifier from a
# trusted authorization source such as a JWT token.

@app.get("/tenant/<tenant_id>")
def get_tenant_data(tenant_id):
    logger.info("get_tenant_data", extra={'tenant_id': tenant_id})
    tenant_session = TenantAbacSession(tenant_id)
    tenant_data_store = TenantDataStore(tenant_session)
    return tenant_data_store.retrieve()

@app.post("/tenant/<tenant_id>")
def post_tenant_data(tenant_id):
    try:
        tenant_data = app.current_event.json_body
    except:
        raise BadRequestError("invalid tenant data")

    logger.info("post_tenant_data", extra={'tenant_id': tenant_id, 'tenant_data': tenant_data})
    tenant_session = TenantAbacSession(tenant_id)
    tenant_data_store = TenantDataStore(tenant_session)
    return tenant_data_store.store(tenant_data)

def lambda_handler(event, context):
    return app.resolve(event, context)