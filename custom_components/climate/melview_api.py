import requests

base_url = 'https://api.melview.net/'
appversion = '3.2.673'

class Heatpump:
	def __init__(self, room, unitid, status):
		self.room = room
		self.unitid = unitid
		self.status = status

class HeatpumpStatus:
	def __init__(self, json):
		self.id = json['id']
		self.power = json['power']
		self.standby = json["standby"]
		self.setmode = json["setmode"]
		self.automode = json["automode"]
		self.setfan = json['setfan']
		self.settemp = json["settemp"]
		self.roomtemp = json['roomtemp']
		self.airdir = json["airdir"]
		self.airdirh = json["airdirh"]
		self.sendcount = json["sendcount"]
		self.fault = json["fault"]
		self.error = json["error"]

	def __str__(self):
		return "id={},power={},standby={},setmode={},automode={},setfan={},settemp={},roomtemp={},airdir={},airdirh={},sendcount={},fault={},error={}".format(
			self.id, self.power, self.standby, self.setmode, self.automode, self.setfan, self.settemp, self.roomtemp, self.airdir, self.airdirh, self.sendcount, self.fault, self.error)

def get_headers(cookie):
	return { 'Cookie': cookie }

def post(cookie, api, data):
	req = requests.post(base_url + api, json=data, headers = get_headers(cookie))
	print("{} result".format(api), req.status_code, req.reason)
	if req.status_code == 200:
		return req.json()
	return None


def login(username, password):
	data = {
		"user": username,
		"pass": password,
		"appversion": appversion
	}
	req = requests.post(base_url + 'api/login.aspx', json=data)
	print('login result', req.status_code, req.reason)
	if req.status_code == 200:
		return req.headers['Set-Cookie']
	return None

def logout():
	req = requests.post(base_url + 'api/logout.aspx')
	print('logout result', req.status_code, req.reason)

def list_rooms(cookie):
	req = requests.get(base_url + 'api/rooms.aspx', headers = get_headers(cookie))
	print('list_rooms result', req.status_code, req.reason)

	if req.status_code != 200:
		return []

	# don't care about buildings, just get the list of units.
	units = req.json()[0]['units']

	heatpumps = []
	
	for unit in units:
		room = unit['room']
		unitid = unit['unitid']

		print('found room', room, unitid)

		status = get_unit_status(cookie, unitid)

		get_unit_capabilities(cookie, unitid)

		if status != None:
			heatpump = Heatpump(room, unitid, status)
			heatpumps.append(heatpump)

	return heatpumps

def get_unit_capabilities(cookie, unitid):
	return post(cookie, "api/unitcapabilities.aspx", { 'unitid': unitid })

def get_unit_status(cookie, unitid):
	data = {
		'unitid': unitid,
		'v': 2
	}
	res = post(cookie, "api/unitcommand.aspx", data)

	if res != None:
		return HeatpumpStatus(res)
	return None

def send_cmd(cookie, unitid, cmd):
	data = {
		'unitid': unitid,
		'v': 2,
		'commands': cmd
	}
	return post(cookie, "api/unitcommand.aspx", data)

def send_set_power(cookie, unitid, power):
	return send_cmd(cookie, unitid, "PW{}".format(power))

def send_set_temp(cookie, unitid, temp):
	return send_cmd(cookie, unitid, "TS{}".format(temp))

def send_set_fan(cookie, unitid, fan):
	return send_cmd(cookie, unitid, "FS{}".format(fan))

def send_set_mode(cookie, unitid, mode):
	return send_cmd(cookie, unitid, "MD{}".format(mode))

def get_room(name):
	for room in config["rooms"]:
		if room["name"].lower() == name.lower():
			return room
	return None

def set_power(unitid, power):
	cookie = login()

	if cookie == None:
		return False
		
	if send_set_power(cookie, unitid, power):
		logout()
		return True

	logout()
	return False

def turn_on(unitid):
	return set_power(unitid, 1)

def turn_off(unitid):
	return set_power(unitid, 0)

def get_temp(name):
	cookie = login()

	if cookie == None:
		return "Failed to Login"

	room = get_room(name)

	if room == None:
		logout()
		return "Failed to find {}".format(name)

	unitid = room["unitid"]

	status = get_unit_status(cookie, unitid)

	if status == None:
		logout()
		return "Failed to get the current heatpump temperature"

	logout()
	return "The current heatpump temperature is {}".format(status.settemp)

def get_room_temp(name):
	cookie = login()

	if cookie == None:
		return "Failed to Login"

	room = get_room(name)

	if room == None:
		logout()
		return "Failed to find {}".format(name)

	unitid = room["unitid"]

	status = get_unit_status(cookie, unitid)

	if status == None:
		logout()
		return "Failed to get the current room temperature"

	logout()
	return "The current room temperature is {}".format(status.roomtemp)

def get_status(unitid):
	cookie = login()

	if cookie == None:
		return "Failed to Login"

	status = get_unit_status(cookie, unitid)

	if status == None:
		logout()
		return "Failed to get the current status"

	logout()
	return status

def set_temp(name, temp):
	cookie = login()

	if cookie == None:
		return "Failed to Login"

	room = get_room(name)

	if room == None:
		logout()
		return "Failed to find {}".format(name)

	unitid = room["unitid"]

	if send_set_temp(cookie, unitid, temp):
		logout()
		return 'Set temperature on the {} heatpump to {} degrees'.format(name, temp)
	logout()
	return 'Failed to set temperature on the {} heatpump'.format(name)


def set_fan(unitid, fan):
	cookie = login()

	if cookie == None:
		return "Failed to Login"

	if send_set_fan(cookie, unitid, fan):
		logout()
		return True
	logout()
	return False

def set_mode(name, mode):
	mode_num = None
	if mode == "heat" or mode == "heating":
		mode = "heat"
		mode_num = 1
	elif mode == "dry":
		mode_num = 2
	elif mode == "cool" or mode == "cooling":
		mode = "cool"
		mode_num = 3
	elif mode == "fan":
		mode_num = 7
	elif mode == "auto":
		mode_num = 8
	else:
		return "I don't know what mode {mode} is"

	cookie = login()

	if cookie == None:
		return "Failed to Login"

	room = get_room(name)

	if room == None:
		logout()
		return "Failed to find {}".format(name)
		
	unitid = room["unitid"]

	if send_set_mode(cookie, unitid, mode_num):
		logout()
		return 'Set mode on the {} heatpump to {}'.format(name, mode)
	logout()
	return 'Failed to set mode on the {} heatpump'.format(name)

STR_MODE_HEAT = 'Heat'
STR_MODE_DRY = 'Dry'
STR_MODE_COOL = 'Cooling'
STR_MODE_FAN = 'Fan'
STR_MODE_AUTO = 'Auto'

MODE_HEAT = 1
MODE_DRY = 2
MODE_COOL = 3
MODE_FAN = 7
MODE_AUTO = 8

def get_mode_name(mode):
	if mode == MODE_HEAT:
		return STR_MODE_HEAT
	elif mode == MODE_DRY:
		return STR_MODE_DRY
	elif mode == MODE_COOL:
		return STR_MODE_COOL
	elif mode == MODE_FAN:
		return STR_MODE_FAN
	elif mode == MODE_AUTO:
		return STR_MODE_AUTO

def get_mode(name):
	if name == STR_MODE_HEAT:
		return 1
	elif name == STR_MODE_DRY:
		return MODE_DRY
	elif name == STR_MODE_COOL:
		return MODE_COOL
	elif name == STR_MODE_FAN:
		return MODE_FAN
	elif name == STR_MODE_AUTO:
		return MODE_AUTO

def get_mode_names():
	return [STR_MODE_HEAT, STR_MODE_DRY, STR_MODE_COOL, STR_MODE_FAN, STR_MODE_AUTO]