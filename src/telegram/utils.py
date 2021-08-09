#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests, json, boto3, subprocess
import polly, transcribe #my libs
from os import environ, remove

# gets the secrets from AWS SSM
def get_secrets(secret_name):
    ssm = boto3.client('ssm')
    parameter = ssm.get_parameter(Name=secret_name, WithDecryption=True)
    return parameter['Parameter']['Value']

# gets the text and sends the voice
def handle_text(uid, msg):
    #print (uid, msg)
    voice_file = polly.get_voice(msg.get("text"))
    send_audio_message(uid, voice_file)
    remove(voice_file)

#get the vocie  and sends the text
def handle_voice(uid, msg):
    voice_file_id = msg["voice"]["file_id"]
    voice_file_path = downlaod_telegram_voice_file(voice_file_id)
    transcribed_result = transcribe.transcribe_voice(voice_file_path)
    #print("transcribed_result", transcribed_result)
    send_text_message(uid, transcribed_result["results"]["transcripts"][0]["transcript"])

# generate the base URL needed for Telegram API calls
def get_telegram_base_api_url():
    ssm_key_name = environ["SSM_TELEGRAM_APIK"]
    apikey = get_secrets(ssm_key_name)
    return "https://api.telegram.org/bot{}".format(apikey)

# generate the base URL needed for Telegram file API calls
def get_telegram_file_base_api_url(filepath):
    ssm_key_name = environ["SSM_TELEGRAM_APIK"]
    apikey = get_secrets(ssm_key_name)
    return "https://api.telegram.org/file/bot{}/{}".format(apikey, filepath)

# sends a text message to Telegram user 
def send_text_message(uid, msg):
    json_data = {
        "chat_id": uid,
        "text": ""
    }

    try:
        json_data["text"] = json.dumps(msg)
    except ValueError as e:
        json_data["text"] = "Error! {}".format(e)

    response = requests.post("{}/sendMessage".format(get_telegram_base_api_url()), json=json_data).json()
    return response

# sends a voice message to Telegram user 
def send_audio_message(uid, audio_file_path):
    json_data = {
        'chat_id': uid,
        'title': 'Converted to speech'
    }
    
    opus_coded_audio_file = convert_to_opus(audio_file_path)
    with open(opus_coded_audio_file, 'rb') as audio:
        files = {
            'voice': audio.read(),
        }
        
        response = requests.post("{}/sendVoice".format(get_telegram_base_api_url()),data=json_data, files=files).json()
        return response

# runs a command
# created this method because we need to run ffmpeg and convert the Polly output file to ogg
def run_command(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

# converting the Polly output to ogg format
def convert_to_opus(input_audio_file):
    output_file = "/tmp/audio.ogg"
    run_command("./ffmpeg -i {} -acodec libopus {} -y".format(input_audio_file, output_file))
    return output_file

# gets the vocie file from Telegram file API
def downlaod_telegram_voice_file(file_id):
    get_file_response = requests.get("{}/getFile?file_id={}".format(get_telegram_base_api_url(), file_id)).json()
    voice_file_path = get_file_response["result"]["file_path"]
    voice_filename = voice_file_path.split("/")[-1]
    download_file_response = requests.get(get_telegram_file_base_api_url(voice_file_path))
 
    temp_voice_path = "/tmp/{}".format(voice_filename)
    with open(temp_voice_path, 'wb') as f:
        f.write(download_file_response.content)

    return temp_voice_path
