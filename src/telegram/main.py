#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json, logging, utils
from os import environ

# takes care of IO
def handler(event, context):
    
    # adding verbos logging
    # this can use a better central logging approach and has to be updated
    if environ["VERBOSE"] == "True": print("event", event)

    try:
        sbody = event.get("body") #string body
        body = json.loads(sbody) #json body

        message = body.get("message")
        uid = body.get("message").get("chat").get("id")
        
        # simple dispatching
        if "text" in message:
            print("processig text.", uid, message)
            print(utils.handle_text(uid, message))
        elif "voice" in message:
            print("processig voice.", uid, message)
            print(utils.handle_voice(uid, message))

        return {'statusCode': 200}

    except Exception as e:
        logging.error(e)
        return e
