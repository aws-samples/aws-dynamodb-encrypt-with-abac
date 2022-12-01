import aws_cdk as core
import aws_cdk.assertions as assertions

from demoapp.demoapp_stack import DemoappStack

# example tests. To run these tests, uncomment this file along with the example
# resource in demoapp/demoapp_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = DemoappStack(app, "demoapp")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
