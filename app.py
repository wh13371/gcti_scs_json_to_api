#!/usr/bin/env python

import datetime, time, json, logging, os, sys, threading, socket
from pprint import pprint

# non default imports
from flask import Flask, make_response, render_template, request, abort, url_for, redirect # pip install flask
from flask import jsonify
import redis # pip install redis

# get ENV VAR settings OR use defaults if not present
FLASK_APP_PORT = os.getenv('FLASK_APP_PORT', 9999)
REDIS_HOST = os.getenv('REDIS_HOST', 'CHANGEME!')
REDIS_PORT = os.getenv('REDIS_PORT', 'CHANGEME!')
REDIS_DB = os.getenv('REDIS_DB', 'CHANGEME!')
REDIS_STREAM = os.getenv('REDIS_STREAM', 'CHANGEME!')

# log <stdout> to a redis stream
RLOG_ENABLED = os.getenv('RLOG_ENABLED', 0)
RLOG_STREAM = os.getenv('RLOG_STREAM', 'CHANGEME!')
RLOG_SIZE = os.getenv('RLOG_SIZE', 1000)

# globals
log = logging.getLogger(__name__)
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
app = Flask(__name__)
APP_NAME="gcti:scs:redis"
__version__ = "Sept.2020"

def get_now():
	return datetime.datetime.now().strftime("%Y:%m:%d %H:%M:%S.%f")

def get_now_iso():
    return datetime.datetime.utcnow().isoformat()

def get_epoch():
	return time.time()

def get_epoch_ns():
	return time.time_ns()

def get_pid():
	return os.getpid()

def get_hostname():
	return socket.gethostname()

def get_appname():
	return APP_NAME

def get_app_uptime():
    secs = get_epoch() - app_start_time
    result = datetime.timedelta(seconds=secs)
    return str(result)

def dd(message, level="INFO", **kwargs):
	log = {'timestamp': get_now(), 'epoch': get_epoch(), 'pid': get_pid(), 'level': level, 'message': message}
	if kwargs: out['kwargs'] = kwargs
	print(log)
	sys.stdout.flush()
	if RLOG_ENABLED:
		_r_id = r.xadd(RLOG_STREAM, log, '*', maxlen=int(RLOG_SIZE))
	return log

###

app_start_time = get_epoch()

def redis_status():
	_redis_ping = r.ping()
	dd(str(_redis_ping)) # bool to str

	_redis_info = r.info()
	dd(json.dumps(_redis_info)) # dict to json str

	return True


@app.route("/", methods=['GET'])
def index():
	return redirect(url_for('rlog'))


@app.route("/info")
def info():
	data = { 
	'hostname': get_hostname(),
	'app-name': get_appname(),
	'app-start-time': app_start_time,
	'app-uptime': get_app_uptime(),
	'pid': get_pid(),
	'request-ts': get_epoch_ns(),
	'version': __version__
	}
	return jsonify(data), 200


@app.route("/scs2redis", methods=['POST'])
def scs_to_redis():

	# get data from the SCS curl output
	scs_alarm_data = request.get_json()
	
	dd(json.dumps(scs_alarm_data))

	# send alarm data to REDIS stream
	_r_id = r.xadd(REDIS_STREAM, scs_alarm_data, '*', maxlen=100) # only keep the last 100 events

	dd("{'redis-id': %s}" % _r_id)

	return jsonify({'redis-id': _r_id.decode()}), 200


@app.route("/log2redis", methods=['GET'])
def log2redis():
	global RLOG_ENABLED
	RLOG_ENABLED = not RLOG_ENABLED
	return jsonify({'RLOG_ENABLED': RLOG_ENABLED, 'RLOG_NAME': RLOG_NAME, 'RLOG_SIZE': RLOG_SIZE}), 200


def xl8(data): # convert [bytes] to [string] for "Types"
    if isinstance(data, bytes): return data.decode('utf-8')
    if isinstance(data, dict): return dict(map(xl8, data.items()))
    if isinstance(data, tuple): return map(xl8, data)
    return data

	
@app.route("/rlog", methods=['GET']) #  return the RLOG STREAM
def rlog():
	r_events = r.xrevrange(RLOG_STREAM, "+", "-")
	data = []
	for k, v in r_events:
		d = {xl8(k): xl8(v)}
		data.append(d)
	
	return jsonify(data), 200


@app.errorhandler(404)
def not_found(error):
	return make_response(jsonify({'error': '404 Not Found'}), 404)


if __name__ == "__main__":
 
	redis_status()

	app.run(host='0.0.0.0', port=FLASK_APP_PORT, debug=False)

