
import json
from aws_cdk import (core, aws_codebuild as codebuild,
            aws_codecommit as codecommit,
            aws_codepipeline as codepipeline,
            aws_codepipeline_actions as codepipeline_actions,
            aws_s3 as s3,
            aws_lambda as lambda_)

class PipelineStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, *, repo_name: str=None,
                 application_code: lambda_.CfnParametersCode=None, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        # In this stack we create the pipeline using CDK
        # We have one pipeline, 2 builds and 1 deployment
        # The pipeline has multiple stages (in this example we have 3 stages: Source, Build, and Deploy)
        # 1 builds is for creating the artifact used for lambda function
        # another build is for creating the cloudformation template and the whole infra

        # reading the buildspecs JSON from file but should also be possible to write it in Python
        with open('./pipeline/buildspecs.json') as f:
            buildspecs = json.load(f)

        ### S3 bucket
        # for build output
        build_output_S3_bucket = s3.Bucket(self, "BUILD_OUTCOME")
        
        # Important Note. It is better not to create the repo in the stack as destroying the stack can delete the repo!!
        code = codecommit.Repository.from_repository_name(self, "ImportedRepo", repo_name)
        
        # buildspec phase name: built. Possible phases: build,install,post_build,pre_build
        cdk_build_spec = codebuild.BuildSpec.from_object(buildspecs["cdk_build_spec"])
        telegram_build_spec = codebuild.BuildSpec.from_object(buildspecs["telegram_build_spec"])
  
        cdk_build = codebuild.PipelineProject(self, "CdkBuild", build_spec=cdk_build_spec)
        telegram_build = codebuild.PipelineProject(self, 'telegram', build_spec=telegram_build_spec)
        
        source_output = codepipeline.Artifact()
        cdk_build_output = codepipeline.Artifact("CdkBuildOutput")
        telegram_build_output = codepipeline.Artifact("TelegramBuildOutput")
        telegram_lambda_location = telegram_build_output.s3_location
        
        pipeline_source_stage = codepipeline.StageProps(stage_name="Source",
                    actions=[
                        codepipeline_actions.CodeCommitSourceAction(
                            action_name="CodeCommit_Source",
                            repository=code,
                            branch="develop",
                            output=source_output)])
        
        pipeline_build_stage = codepipeline.StageProps(stage_name="Build",
                    actions=[
                        codepipeline_actions.CodeBuildAction(
                            action_name="telegram_build",
                            project=telegram_build,
                            input=source_output,
                            outputs=[telegram_build_output]),
                        codepipeline_actions.CodeBuildAction(
                            action_name="CDK_Build",
                            project=cdk_build,
                            input=source_output,
                            outputs=[cdk_build_output])
                    ])

        pipeline_deploy_stage_action1 = codepipeline_actions.CloudFormationCreateUpdateStackAction(
                            action_name="Lambda_CFN_Deploy",
                            template_path=cdk_build_output.at_path("EnEchoBot.template.json"),
                            stack_name="TelegramDeploymentStack",
                            admin_permissions=True,
                            parameter_overrides=dict(
                                application_code.assign(
                                    bucket_name=telegram_lambda_location.bucket_name,
                                    object_key=telegram_lambda_location.object_key,
                                    object_version=telegram_lambda_location.object_version)),
                            extra_inputs=[telegram_build_output])

        pipeline_deploy_stage = codepipeline.StageProps(stage_name="Deploy", actions=[pipeline_deploy_stage_action1])

        codepipeline.Pipeline(self, "Pipeline", stages=[pipeline_source_stage, pipeline_build_stage, pipeline_deploy_stage], artifact_bucket=build_output_S3_bucket)