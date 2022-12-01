
# How to secure your SaaS tenant data in DynamoDB with ABAC and client-side encryption

## Summary

This repository contains the code for the solution described in the AWS blog post [How to secure your SaaS tenant data in DynamoDB with ABAC and client-side encryption](https://aws.amazon.com/blogs/security/how-to-secure-your-saas-tenant-data-in-dynamodb-with-abac-and-client-side-encryption/).

## Deploying and testing the solution

### Prerequisites

To deploy and test the solution, you need the following:

* An AWS account
*  The [AWS Command Line Interface (AWS CLI)](https://aws.amazon.com/cli/)
* NodeJS version [compatible with AWS CDK](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html#getting_started_prerequisites) version 2.37.0
* Python3.9
* Git command
* Docker

### Deploying the solution

After you have the prerequisites installed, run the following steps in a command line environment to deploy the solution. Make sure that your AWS CLI is configured with your AWS account credentials. Note that standard AWS service charges apply to this solution. For more information about pricing, see the [AWS Pricing](https://aws.amazon.com/pricing/) page.

1. Use the following command to download this source code:

```
git clone https://github.com/aws-samples/aws-dynamodb-encrypt-with-abac
cd aws-dynamodb-encrypt-with-abac
```

2. (Optional) You will need an AWS CDK version compatible with the application (2.37.0) to deploy. The easiest way is to install a local copy with npm, but you can also use a globally installed version if you already have one. To install locally, use the following command to use npm to install the AWS CDK:

```
npm install cdk@2.37.0
```

3. Use the following commands to initialize a Python virtual environment:

```
python3 -m venv demoenv
source demoenv/bin/activate
python3 -m pip install -r requirements.txt
```

4. (Optional) If you have not used AWS CDK with this account and Region before, you first need to bootstrap the environment:

```
npx cdk bootstrap
```

5. Use the following command to deploy the application with the AWS CDK:

```
npx cdk deploy
```

6. Make note of the API endpoint URL https://<api url>/prod/ in the Outputs section of the CDK command. You will need this URL for the next steps.

```
Outputs:
DemoappStack.ApiEndpoint4F160690 = https://<api url>/prod/
```

### Testing the solution with example API calls

With the application deployed, you can test the solution by making API calls against the API URL that you captured from the deployment output. You can start with a simple HTTP POST request to insert data for a tenant. The API expects a JSON string as the data to store, so make sure to post properly formatted JSON in the body of the request.

```
curl https://<api url>/prod/tenant/<tenant-name> -X POST --data '{"email":"<tenant-email@example.com>"}'
```

We can then read the same data back with an HTTP GET request:

```
curl https://<api url>/prod/tenant/<tenant-name>
```

You can store and retrieve data for any number of tenants, and can store as many attributes as you like. Each time you store data for a tenant, any previously stored data is overwritten.
