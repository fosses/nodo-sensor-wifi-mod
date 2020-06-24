from os import listdir
from ujson import load
from gc import collect
from sys import print_exception

initialized	=	False
data		=	""

def readCfg(logger=None):
	global initialized,data
	data_sbx	=	{}
	if not initialized:
		file_partition	= "/fc"
		file_name		= "cfg.json"
		file_pub		= "publishers.json"
		file_pub_rute	= "%s/%s"%(file_partition,file_pub)
		try:
			if file_name in listdir(file_partition):
				file_name = file_partition + "/" + file_name
			else:
				file_name= "cfge.json"
		except Exception as e:
			print("No se encontro el archivo de config debido a: %s. Se importara el archivo por defecto" %(repr(e)))
			file_name= "cfge.json"
		print("Importando desde archivo de configuracion %s" %file_name)
		with open(file_name) as json_data_file:
			data = load(json_data_file)
		if file_name is not "cfge.json" and "scinadmin" in data:
			print("Iniciando Scinadmin")
			import lib.scinabox as scinabox
			device   = 	scinabox.ScinaboxAdmin(
				host	=	data["scinadmin"]["host"], 
				port	=	data["scinadmin"]["port"], 
				email	=	data["scinadmin"]["email"], 
				password=	data["scinadmin"]["password"])
######			if logger is not None:
######				logger.enableRemoteStatus(device)	
			print("Buscando actualizaciones de publicadores")
			data_sbx=device.find_data()
			if device.login():
				print("Logged in !")
				print("Token: %s"%device.user["token"])
				data_sbx_new=device.update(data["scinadmin"]["auth_key"],data_sbx["updatedAt"])
				if data_sbx_new is not None:	
					del data_sbx
					data_sbx=data_sbx_new
					del data_sbx_new
			else:
				print("No se pudo autenticar en scinadmin :c")
			if data_sbx["updatedAt"] is not None and 'config' in data_sbx:
				data["attributes"]=data_sbx['config']['attributes']
				data["publishers"]=data_sbx['config']['publishers']
				del data["attributes"]["_id"]
#				print (data["attributes"])
#				print (data["publishers"])
				del data_sbx
			else:
				print("No hay publicadores ni atributos desde Scinadmin")
		logger.startTelegram(data["attributes"]["nombre"])
		initialized = True
#	return data

def findPublisher(publisher_name):
	for pub in publishers():
		if pub["name"] == publisher_name:
			return pub
	return None

def publishers(logger):
	print("importando publicadores")
	readCfg(logger)
	return data["publishers"]


def measurements():
	print("importando formato de mediciones")
	readCfg()
	return data["measurements"]

def attributes():
	print("importando atributos de publicadores")
	readCfg()
	return data["attributes"]
	
def readjson(file_name): 
#	file_name = "/fc/wifi.json"
	with open(file_name) as json_data_file:
		data = load(json_data_file)
	return data
def readbuses():
	conf = readCfg()
	return conf["buses"]	
