
import yaml

from aws_cdk import (core,
                    aws_s3 as s3,
                    aws_codedeploy as codedeploy,
                    aws_ssm as ssm,
                    aws_iam as iam,
                    aws_lambda as lambda_)

from aws_cdk.aws_apigateway import (
    RestApi, 
    LambdaIntegration,
    MockIntegration,
    PassthroughBehavior
)

from aws_cdk.aws_lambda import (
    Function,
    Runtime
)

class EnEchoBotStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.application_code = lambda_.Code.from_cfn_parameters()

        # just to show we can use config files for different environments
        with open("pipeline/config.yml", 'r') as stream:
            configs = yaml.safe_load(stream)

        ### S3 bucket 
        #for keeping temp audio files and possible other usecases
        S3_bucket = s3.Bucket(self, "enecho")

        ### api gateway core
        api_gateway = RestApi(self, 'ENECHO_API_GATEWAY', rest_api_name='EnEchoBotApiGateway')
        api_gateway_resource = api_gateway.root.add_resource(configs["ProjectName"])
        api_gateway_telegram_resource = api_gateway_resource.add_resource('telegram')
        
        # for security reason we do not want to keep API Key in the code so we manage them in AWS System Manager (SSM)
        ssm_temp_telegram_apik_param = ssm.StringParameter(self, "TELEGRAM_API_KEY",
            string_value="None", 
            description="The API Key used for integrating with Telegram. Need manual override. Default is None."
        )
        
        ### additional policies
        # not a good idea to use wildcard (*) for resources. has to be changed.
        polly_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW, 
            resources=['*'],
            actions=['polly:SynthesizeSpeech']
            )
        
        #resources has to be updated
        transcribe_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW, 
            resources=['*'],
            actions=["transcribe:StartTranscriptionJob",
                "transcribe:GetTranscriptionJob",
                "transcribe:DeleteTranscriptionJob"]
            )

        ### handle telegram requests function
        telegram_function = Function(self, "ENECHO_TELEGRAM_PROC",
            function_name="ENECHO_TELEGRAM_PROC",
            environment={
                "SSM_TELEGRAM_APIK": ssm_temp_telegram_apik_param.parameter_name,
                "VERBOSE": "False",
                "S3_BUCKET": S3_bucket.bucket_name

            },
            runtime=Runtime.PYTHON_3_7,
            timeout=core.Duration.seconds(60),
            handler="main.handler",
            # code=Code.asset("./src/telegram")) 
            code=self.application_code)

        alias = lambda_.Alias(self, "LambdaAlias", alias_name="Prod", version=telegram_function.current_version)
        S3_bucket.grant_read_write(telegram_function)
        S3_bucket.grant_delete(telegram_function)

        # Lambda function deployment configs
        codedeploy.LambdaDeploymentGroup(self, "DeploymentGroup",
            alias=alias,
            deployment_config=codedeploy.LambdaDeploymentConfig.LINEAR_10_PERCENT_EVERY_1_MINUTE
        )

        # API Gateway integration with Lambda function
        telegram_integration = LambdaIntegration(
            telegram_function, 
            proxy=True, 
            integration_responses=[{
                'statusCode': '200',
               'responseParameters': {
                   'method.response.header.Access-Control-Allow-Origin': "'*'",
                }
            }])

        api_gateway_telegram_resource.add_method('POST', telegram_integration,
            method_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Access-Control-Allow-Origin': True,
                }
            }]
            )

        telegram_function.add_to_role_policy(polly_policy)
        telegram_function.add_to_role_policy(transcribe_policy)      
        ssm_temp_telegram_apik_param.grant_read(telegram_function)

        ### API gateway finalizing
        self.add_cors_options(api_gateway_telegram_resource)

    def add_cors_options(self, apigw_resource):
        apigw_resource.add_method('OPTIONS', MockIntegration(
            integration_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                    'method.response.header.Access-Control-Allow-Origin': "'*'",
                    'method.response.header.Access-Control-Allow-Methods': "'POST,OPTIONS'"
                }
            }
            ],
            passthrough_behavior=PassthroughBehavior.WHEN_NO_MATCH,
            request_templates={"application/json":"{\"statusCode\":200}"}
        ),
        method_responses=[{
            'statusCode': '200',
            'responseParameters': {
                'method.response.header.Access-Control-Allow-Headers': True,
                'method.response.header.Access-Control-Allow-Methods': True,
                'method.response.header.Access-Control-Allow-Origin': True,
                }
            }
        ],
    )