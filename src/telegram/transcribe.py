# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import time, requests

from requests.models import Response
import boto3
from os import environ, remove

def transcribe_file(job_name, file_uri, transcribe_client):
    transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': file_uri},
        MediaFormat='ogg',
        LanguageCode='en-US'
    )

    max_tries = 60
    file_url = ""
    while max_tries > 0:
        max_tries -= 1
        job = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
        job_status = job['TranscriptionJob']['TranscriptionJobStatus']
        if job_status in ['COMPLETED', 'FAILED']:
            print(f"Job {job_name} is {job_status}.")
            if job_status == 'COMPLETED':
                file_url = job['TranscriptionJob']['Transcript']['TranscriptFileUri']
                # print(
                #     f"Download the transcript from\n"
                #     f"\t{job['TranscriptionJob']['Transcript']['TranscriptFileUri']}.")
            break
        else:
            print(f"Waiting for {job_name}. Current status is {job_status}.")
        time.sleep(3)
    
    return file_url

def uplaod_to_s3(local_file_path):
    s3 = boto3.resource('s3')
    s3_bucket = environ["S3_BUCKET"]
    local_filename = local_file_path.split("/")[-1]
    s3_object_path = "tmp/telegram_voice/{}".format(local_filename)
    s3_uri = "s3://{}/{}".format(s3_bucket, s3_object_path)

    s3.Bucket(s3_bucket).upload_file(local_file_path, s3_object_path)
    return s3_uri

def delete_s3_object(file_uri):
    s3 = boto3.resource('s3')
    s3_bucket = environ["S3_BUCKET"]
    s3_object_path = file_uri.split("/")[-1].replace("{}/".format(s3_bucket), "")
    s3.delete_object(Bucket=s3_bucket, Key=s3_object_path)

def transcribe_voice(file_path):
    transcription_job_name = "telegram_voice_transcribe_job_{}".format(int(time.time()))
    transcribe_client = boto3.client('transcribe')
    file_uri = uplaod_to_s3(file_path)
    transcibe_response = transcribe_file(transcription_job_name, file_uri, transcribe_client)
    transcription_result = requests.get(transcibe_response).json()

    remove(file_path)
    transcribe_client.delete_transcription_job(TranscriptionJobName=transcription_job_name)
    return transcription_result
