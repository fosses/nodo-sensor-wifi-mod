# This file is executed on every boot (including wake-boot from deepsleep)
from gc import collect
from esp import osdebug
from time import sleep
from ujson import load
import webrepl
from uos import mount, umount
from machine import unique_id, SDCard

osdebug(None)
collect()

try:
	mount(SDCard(slot=2, width=1, sck=14, miso=15, mosi=13, cs=5), "/fc")
	SD=True
	print("SD mounted")
except Exception as e:
	SD=False
	print("SD not mounted")
	
def readwificfg(): 
	try:
		file_name = "/fc/wifi.json"
		with open(file_name) as json_data_file:
			data = load(json_data_file)
		return data
	except Exception as e:
		print(repr(e))
		return None
def get_id():
	x = [hex(int(c)).replace("0x","") for c in unique_id()]
	for i in range(len(x)):                                                                                                                           
		if len(x[i]) == 1:
			x[i] = "0"+x[i]
	return ''.join(x)
  
def do_connect():
	import network
	wlan = network.WLAN(network.STA_IF) # create station interface
	wlan.active(True)	   # activate the interface
	wlan.config(dhcp_hostname="ESP32_NODO_" + get_id())
	if not wlan.isconnected():	  # check if the station is connected to an AP
		wlan.connect(wficfg["ssid"], wficfg["pssw"]) # connect to the AP (Router)
		for _ in range(30):
			if wlan.isconnected():	  # check if the station is connected to an AP
				print('\nNetwork config:', wlan.ifconfig())
				webrepl.start()
#				import uftpd
				break
			print('.', end='')
			sleep(1)
		else:
			print("\nConnect attempt timed out\n")
			return
	else:
		print("Already connected")
		print('\nNetwork config:', wlan.ifconfig())
	
wficfg=None
if SD:
	print("Reading Wi-Fi data from SD")
	wficfg=readwificfg()
if not SD or wficfg is None:
	print("Reading default Wi-Fi data")
	wficfg = {}
	wficfg["ssid"]="WSLAB"
	wficfg["pssw"]="wslabufro"
	
do_connect()
if SD:
	umount('/fc')
	print("SD unmounted")
collect()

# print('Booted!')

