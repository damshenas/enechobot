# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Getting Started Example for Python 2.7+/3.3+ 
from contextlib import closing
import os
from tempfile import gettempdir
import os
import boto3

def get_voice(text):
    polly = boto3.client("polly")
    response = polly.synthesize_speech(Text=text, OutputFormat="ogg_vorbis", VoiceId="Joanna")
    audio_file_path = os.path.join(gettempdir(), "speech.ogg")
    if "AudioStream" in response:
        # Note: Closing the stream is important because the service throttles on the
        # number of parallel connections. Here we are using contextlib.closing to
        # ensure the close method of the stream object will be called automatically
        # at the end of the with statement's scope.
        with closing(response["AudioStream"]) as stream:
            with open(audio_file_path, "wb") as file:
                file.write(stream.read())
                
        return audio_file_path

def break_text(rest):
    #Because single invocation of the polly synthesize_speech api can 
    # transform text with about 1,500 characters, we are dividing the 
    # post into blocks of approximately 1,000 characters.
    textBlocks = []
    while (len(rest) > 1100):
        begin = 0
        end = rest.find(".", 1000)

        if (end == -1):
            end = rest.find(" ", 1000)
            
        textBlock = rest[begin:end]
        rest = rest[end:]
        textBlocks.append(textBlock)
    textBlocks.append(rest)     
    
    return textBlocks
