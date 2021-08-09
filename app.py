#!/usr/bin/env python3

from aws_cdk import core

from pipeline.pipeline_stack import PipelineStack
from pipeline.application_stack import EnEchoBotStack

app = core.App()

# main stack configs
application_stack = EnEchoBotStack(app, "EnEchoBot", env={'region': 'eu-central-1'})

PipelineStack(app, "PipelineDeployingApplicationStack",
    env={'region': 'eu-central-1'},
    application_code=application_stack.application_code,
    repo_name="EnEchoBot")

app.synth()