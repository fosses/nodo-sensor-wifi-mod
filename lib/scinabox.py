
from sys import print_exception
import urequests as requests
from uos import listdir
#import ujson as json
from ujson import dumps, load

def mkdir_rec(dir_):
	import os
	path = ""
	for spath in dir_.split("/"):
		path += spath
		try:
			os.mkdir(path)
		except Exception as e:
			pass
		path += "/"
	del os

class ScinaboxAdmin:
	def __init__(self, host = None, port = 8080, email = None, password = None):
		self.host			= host
		self.port			= port
		self.email			= email
		self.password		= password
		self.file_partition	= "/fc"
		self.file_pub		= "publishers.json"
		self.file_pub_rute	= "%s/%s"%(self.file_partition,self.file_pub)
		


	def login(self):
		headers = {'content-type': 'application/json'}
		try:
			r = requests.post(
				url	 = "http://%s:%d/api/user/login"%(self.host, self.port),
				data	= dumps({"email": self.email, "pass": self.password}),
				headers = headers
				
			)
			print(r.json()["message"])
			user = r.json()
			self.user = user
			return r.status_code == 200
		except Exception as e:
			print_exception(e)	
			self.user = None
			return False


	def get_device(self, auth_key):
		self.auth_key=auth_key
		headers = {'content-type': 'application/json', "Authorization": self.user["token"]}
		try:
			r = requests.get(
				url	 = "http://%s:%d/api/user/get-device?auth_key=%s"%(self.host, self.port,auth_key),
#				params  = device,
				headers = headers	
			)  
			print(r.json()["message"])
			print(r.json()["device"])
			return r.json()["device"]
		except Exception as e:
			print_exception(e)	
			return None
			
	def update(self,auth_key,updatedAt=None):
		device=self.get_device(auth_key)
		print("Fecha Pub local: %s\nFecha Pub remoto: %s" %(updatedAt, device["updatedAt"]))
		if updatedAt != device["updatedAt"]:
			print("Cambio en publicadores detectado. Actualizando desde servidor...")
			from os import remove, listdir
			if self.file_pub in listdir(self.file_partition):
				remove(self.file_pub_rute)
				print("Archivo antiguo eliminado")
			else:
				print("No se enconto archivo %s" %self.file_pub_rute)
				try:
					with open(self.file_pub_rute,'w') as f:
						f.write(dumps(device))
					print("Configuración del dispositivo actualizada a %s"%device["updatedAt"])
					return device
				except Exception as e:
					print("No se pudo actualizar la configuración del dispositivo debido a :%s"%repr(e))
					return device
		else:
			return None
		
	def find_data(self):
		print("Buscando archivo %s"%self.file_pub_rute)
		try:
			if self.file_pub in listdir(self.file_partition):
				print("Datos previos de Scinadmin encontrados")
				with open(self.file_pub_rute) as json_data_file:
					data_sbx = load(json_data_file)
			else:
				raise Exception("El archivo %s no existe"%self.file_pub_rute)
		except Exception as e:
			print_exception(e)
			print("No se encontraron datos previos de Scinadmin")
			data_sbx = {}
			data_sbx["updatedAt"]=None
		return data_sbx
		
	def set_device_state(self,state, state_message):
		headers = {'content-type': 'application/json', "Authorization": self.user["token"]}
		try:
			r = requests.post(
				url	 = "http://%s:%d/api/user/set-device-state"%(self.host, self.port),
				data	= dumps({"auth_key": self.auth_key, "state":state , "state_message":state_message}),
				headers = headers	
			)
			print(r.json()["message"])
			return r.status_code == 200
		except Exception as e:
			print_exception(e)	
			return False
