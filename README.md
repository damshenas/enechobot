# An example bot to show a fully serverless service using AWS CDK. The CI/CD is also completely on AWS.



1- Add IAM user for manual deployment of the pipeline

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "cloudformation:*"
            ],
            "Resource": "*",
            "Effect": "Allow"
        },
        {
            "Condition": {
                "ForAnyValue:StringEquals": {
                    "aws:CalledVia": [
                        "cloudformation.amazonaws.com"
                    ]
                }
            },
            "Action": [
                "s3:*",
                "cloudformation:*",
                "lambda:*",
                "iam:*",
                "apigateway:*",
                "dynamodb:*",
                "sts:*",
                "codecommit:*",
                "codepipeline:*",
                "codebuild:*",
                "kms:*",
                "events:*"
            ],
            "Resource": "*",
            "Effect": "Allow"
        },
        {
            "Action": "s3:*",
            "Resource": "arn:aws:s3:::cdktoolkit-stagingbucket-*",
            "Effect": "Allow"
        }
    ]
}
```

2- Add user for git to commit code
3- Create code commit repo 
4- Update the code in app.py
