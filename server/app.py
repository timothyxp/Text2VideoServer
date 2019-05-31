# This Python file uses the following encoding: utf-8

import json

from flask import Flask

from utils.logging.logger import logger

app = Flask("__app__", static_folder='tmp', static_url_path='')

working_status = {}
try:
    with open('working-status.json', 'r') as inp:
        data = inp.read()
        working_status = json.loads(data)
except:
    logger.error('File working-status.json not found')

if not 'max_video_index' in working_status:
    working_status['max_video_index'] = 0
    
def setReadyStatus(current_id, res_file):
    if current_id == None:
        return
    working_status[current_id]['status'] = 'ready'
    working_status[current_id]['url'] = res_file


def setProcessStatus(current_id, message):
    if current_id == None:
        return
    working_status[current_id]['status'] = 'process'
    working_status[current_id]['message'] = message


def setErrorStatus(current_id, error):
    if current_id == None:
        return
    working_status[current_id]['status'] = 'error'
    working_status[current_id]['error'] = error

def saveWorkingStatus():
    with open('working-status.json', 'w') as out:
        out.write(json.dumps(working_status))

def setRenderTimestamp(current_id, renderTimestamp):
    working_status[current_id]['renderTimestamp'] = renderTimestamp
    saveWorkingStatus()

def setRenderTime(current_id, renderTime):
    working_status[current_id]['renderTime'] = renderTime
    saveWorkingStatus()

def saveTimings(current_id, timings):
    working_status[current_id]['timings'] = timings
    saveWorkingStatus()


def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Origin, X-Requested-With, Content-Type, Accept"
    response.headers['Access-Control-Allow-Methods'] = "DELETE, GET, POST, PUT, OPTIONS"
    return response


app.after_request(add_cors_headers)
