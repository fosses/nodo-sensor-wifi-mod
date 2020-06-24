from ujson import dumps, load
from utime import sleep, time, ticks_ms
from sys import print_exception
from os import VfsFat, mount, listdir, umount,remove
import lib.sdcard as sdcard
import _time
from gc import collect
from ucollections import deque

class Logger:
	PARTITION 	= '/fc'
	DEBUG_FILE	= 'debug.txt'
	INFO_FILE 	= 'info.txt'
	WARNING_FILE= 'warning.txt'
	ERROR_FILE	= 'error.txt'
	WIFI_FILE	= 'wifi.json'
	
	def __init__(self, spi = None, cs = None, telegramToken = None, chatId = None, name = "unnamed"):
		self.spi			= spi
		self.cs				= cs
		self.telegramToken 	= telegramToken
		self.chatId			= chatId
		self.name			= name
		self.tgramActive	= False
		self.rStatusActive	= False
		
		try:
			self.sd				= sdcard.SDCard(spi, cs) # Compatible with PCB 
			self.vfs			= VfsFat(self.sd)
			mount(self.vfs, Logger.PARTITION)			
			self.initialized	= True
			print("SD inicializada")
			
		except Exception as e:
			print("No se pudo montar micro SD")
			self.vfs			= None
			self.initialized	= False
			print_exception(e)
			print(repr(e))
	
	def startTelegram(self,name):
		try:
			if self.name is "unnamed":
				val_cfg				= self.readCfg("cfg.json")
				self.telegramToken 	= val_cfg["msgconf"]["token"]
				self.chatId			= val_cfg["msgconf"]["chat_id"]
				self.name			= name
				self.tgramActive	= True
				del val_cfg
				print("Cliente de mensajeria configurado correctamente")
				from lib.requests import post
		except Exception as e:
			print("No se pudo configurar el cliente de mensajeria debido a: %s" %repr(e))
	
	def _log(self, file_path, data_str, e=None, put_timestamp = True, prefix = None, mode ='a'):
		if prefix is not None:
			print(data_str)
		if self.isInitialized():
			try:
				fn = Logger.PARTITION +"/"+ file_path # 'logdev.txt'
				with open(fn,mode) as f:
					if prefix is not None:
						f.write("%s: "%prefix)
					if put_timestamp:
						f.write(_time.now())
					f.write(data_str) 
					f.write("\r\n")
					if e is not None:
						print_exception(e,f)
				sleep(0.2)
			except Exception as e:
				print(repr(e))
	def success(self, data_str):
		if self.rStatusActive:
			self.sendRemoteMessage("SUCCESS",data_str,True)
	def debug(self, data_str,e=None):
		self._log(Logger.DEBUG_FILE, data_str, e, put_timestamp = True, prefix = "DEBUG")
	def info(self, data_str,e=None):
		self._log(Logger.INFO_FILE, data_str, e, put_timestamp = True, prefix = "INFO")
	def warning(self, data_str,e=None):
		self._log(Logger.WARNING_FILE, data_str, e, put_timestamp = True, prefix = "WARNING")
		self.sendRemoteMessage("WARNING",data_str,True)		
	def error(self, data_str,e=None):
		self._log(Logger.ERROR_FILE, data_str, e, put_timestamp = True, prefix = "ERROR")
		self.sendRemoteMessage("ERROR",data_str,False)
		
	def sendRemoteMessage(self, prefix, data_str,onlyRstatus=False):
		if self.rStatusActive:
			try:
				self.remoteStatus.set_device_state(prefix, data_str)
			except Exception as e:
				print("No se pudo enviar mensaje de reporte de error por set_device_state")
				print_exception(e)
		if self.tgramActive and not onlyRstatus:
			data_str= "%s: %s" %(self.name, data_str)
			headers = {'Content-Type': 'application/json','Accept': 'application/json'}
			data 	= {"chat_id": self.chatId, "text": data_str}
			url 	= 'https://api.telegram.org/bot%s/sendMessage'%(self.telegramToken)
			try:
				collect()
				r = post(url = url, data = dumps(data), headers = headers)
#				return r.status_code == 200
			except Exception as e:
				collect()
				print("No se pudo enviar mensaje de reporte de error por telegram")
				print_exception(e)

	def data(self, file_name, data, header =None):
		if header is not None and not file_name in os.listdir(Logger.PARTITION):
				self._log(file_name, header, put_timestamp = False,prefix = None)
		self._log(file_name, data, put_timestamp = False,prefix = None)
	def isInitialized(self):
		return self.initialized
	def readLinesCbk(self, file_name, cbk,uart, uart2, i2c, spi, logger, hpma_pin, pms_pin, publishers, atrpub):
		tstart=time()-(ticks_ms()/1000)
		print("Intentando publicar datos pendientes de %s..." %file_name)
		if self.vfs is not None:
			#os.mount(vfs, '/fc')
			if (file_name in listdir('/fc')):
				fn = '/fc/' + file_name
				print("Publicando datos de: " + file_name)
				print("Buscando indice de Pub.Dif. anterior...")
				if file_name+'_idx' in listdir('/fc'):
					with open(Logger.PARTITION + "/" + file_name+'_idx','r') as file_idx:
						index_pub = int(file_idx.readline())
						print("indice encontrado: %d" %index_pub)
				else:
					print("indice no encontrado. Valor por defecto: 0")
					index_pub=0
				counter=0
				with open(fn,'r') as f:
					for line in f:
						if counter >= index_pub:
							print("Prox ciclo: %i seg" %((tstart + 590)-time()))
							if (time() >= (tstart + 590)):
								from main import readandpublish
								readandpublish(None, uart, uart2, i2c, spi, logger, hpma_pin, pms_pin, publishers, atrpub)
								tstart=time()
							print("\nPublica diferido: %s" %line.strip('\r\n'))
							if (not cbk(line[line.index("{"):].strip('\r\n'))):
								print("No se pudo seguir publicando dados de %s Indice guardado para proximo ciclo: %d" %(file_name,counter))
								self._log(file_name+"_idx", str(counter), put_timestamp = False, mode ='w')
								return True
							if counter%31 >=30:
								self._log(file_name+"_idx", str(counter), put_timestamp = False, mode ='w')
							counter +=1
						else:
							counter +=1
						# publisher.publish(line.strip('\r\n'), attr)
				# c.disconnect()
				print("Datos de %s publicados correctamente" %file_name)
				return False
				#os.remove(fn)
			else: 
				print("No existe el archivo %s" %file_name)
			#os.umount('/fc')
			#utime.sleep(0.2)
		else:
			print("No hay SD para leer la database " + file_name)
		return True
		
	def close(self):
		if self.vfs is not None:
			umount('/fc')
			print("SD Desmontada")
 
	def readCfg(self, file_name):		
		if self.isInitialized():
			try:
				with open(Logger.PARTITION + "/" + file_name) as json_data_file:
					data = load(json_data_file)
				return data
			except Exception as e:
				print(repr(e))
				print("Error importando archivo %s" %file)
				return None
		else:
			print("No iniciado")
			return None
	def removeFile(self, filename):
		remove(self.PARTITION + "/" +filename)
		
	def enableRemoteStatus(self,device):
		self.remoteStatus= device
		self.rStatusActive=True
		print("Remote status habilitado")