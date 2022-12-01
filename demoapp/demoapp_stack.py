# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import (
    # Duration,
    Stack,
    BundlingOptions,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_kms as kms,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_logs as logs,
)
from cdk_nag import NagSuppressions
from constructs import Construct

class DemoappStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        demo_table = dynamodb.Table(self, 'DemoTable',
            partition_key=dynamodb.Attribute(name='tenant_id', type=dynamodb.AttributeType.STRING),
        )

        demo_key = kms.Key(self, 'DemoKey',
            enable_key_rotation=True,
        )

        demo_fn = lambda_.Function(self, 'DemoFunction',
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="index.lambda_handler",
            code=lambda_.Code.from_asset(
                "resources/demo_fn",
                bundling=BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_9.bundling_image,
                    command=[
                        "bash", "-c",
                        "pip install --no-cache -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ],
                ),
            ),
            environment={
                'DEMO_TABLE_NAME': demo_table.table_name,
                'DEMO_KEY_ID': demo_key.key_id,
                # For demonstration and testing purposes, the function logs the full lambda
                # event to CloudWatch. Consider disabling this for any production workload.
                'POWERTOOLS_LOGGER_LOG_EVENT': 'True',
            },
        )
        assert demo_fn.role is not None

        # The policy for the ResourceAccessRole. The policy statements with 
        # tenant-scoped conditions implement the core ABAC functionality that
        # enable the per-tenant access.

        resource_access_policy = iam.ManagedPolicy(self, 'ResourceAccessPolicy',
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "dynamodb:DescribeTable",
                        "dynamodb:GetItem",
                        "dynamodb:PutItem",
                    ],
                    resources=[
                        demo_table.table_arn,
                    ],
                    conditions={
                        "ForAllValues:StringEquals": {
                            "dynamodb:LeadingKeys": [
                                "${aws:PrincipalTag/TenantID}"
                            ]
                        }
                    },
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "kms:Decrypt",
                        "kms:GenerateDataKey",
                    ],
                    resources=[demo_key.key_arn],
                    conditions={
                        "StringEquals": {
                            "kms:EncryptionContext:tenant_id": "${aws:PrincipalTag/TenantID}",
                        }
                    }
                ),
            ]
        )
        
        # The ResourceAccessRole. This role is assumed by the lambda function,
        # and used to access the DynamoDB table, as well as encrypt and 
        # decrypt data with our KMS key.

        resource_access_role = iam.Role(self, 'ResourceAccessRole',
            assumed_by=demo_fn.role.grant_principal,
            managed_policies=[resource_access_policy],
        )
        assert resource_access_role.assume_role_policy is not None

        # The assume role policy for the ResourceAccessRole must also permit
        # sts:TagSession, so that our application can set the appropriate
        # tenant_id tag when assuming the role.

        resource_access_role.assume_role_policy.add_statements(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["sts:TagSession"],
                principals=[demo_fn.role.grant_principal],
                conditions={
                    "StringLike": {
                        "aws:RequestTag/TenantID": "*",
                    }
                }
            )
        ) 

        # Add to the lambda function's execution role the policy statement
        # that allows it to assume the ResourceAccessRole.
        demo_fn.role.add_to_principal_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["sts:AssumeRole"],
            resources=[resource_access_role.role_arn],
        ))

        demo_fn.add_environment(
            key='RESOURCE_ACCESS_ROLE_ARN',
            value=resource_access_role.role_arn,
        )

        api_log_group = logs.LogGroup(self, 'ApiLogs',
            retention=logs.RetentionDays.ONE_MONTH,
        )

        api = apigateway.RestApi(self, 'Api',
            rest_api_name="DemoAppApi",
            description="DemoApp REST API",
            deploy_options=apigateway.StageOptions(
                access_log_destination=apigateway.LogGroupLogDestination(api_log_group),
                access_log_format=apigateway.AccessLogFormat.json_with_standard_fields(
                    caller=True,
                    http_method=True,
                    ip=True,
                    protocol=True,
                    request_time=True,
                    resource_path=True,
                    response_length=True,
                    status=True,
                    user=True
                ),
                logging_level=apigateway.MethodLoggingLevel.INFO,
            )
        )

        lambda_proxy = api.root.add_resource('{proxy+}')
        method = lambda_proxy.add_method('ANY', apigateway.LambdaIntegration(demo_fn),
            request_validator_options=apigateway.RequestValidatorOptions(
                request_validator_name="all",
                validate_request_body=True,
                validate_request_parameters=True,
            )
        )

        # Suppress certain cdk_nag findings that can be ignored in a demo
        # implementation. Note that these should not be automatically ignored
        # for a production implementation!
        NagSuppressions.add_stack_suppressions(
            self,
            [
                {
                    'id': 'AwsSolutions-APIG3',
                    'reason': 'WAF not implemented; demo application',
                },
                {
                    'id': 'AwsSolutions-APIG4',
                    'reason': 'Authorization not implemented; demo application'
                },
                {
                    'id': 'AwsSolutions-COG4',
                    'reason': 'Authorization not implemented; demo application'
                },
                {
                    'id': 'AwsSolutions-IAM4',
                    'reason': 'Use of AWS managed policies is fit-for-purpose for this demo application',
                },
                {
                    'id': 'AwsSolutions-DDB3',
                    'reason': 'Point-in-time-recovery not implemented; demo application',
                },
            ]
        )


