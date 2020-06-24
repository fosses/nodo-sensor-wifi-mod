#from umqtt.simple import MQTTClient
from ujson import dumps, loads
import  lib.requests as requests

class Publisher():
	ATTRIBUTE_URL = "v1/devices/me/attributes"
	TELEMETRY_URL = "v1/devices/me/telemetry"

	def __init__(self, host = "", token = "", port = 1883, format_ = "", logger = None, wdt = None):
		self.host   = host
		self.token  = token
		self.port   = port
		self.format = format_
		self.logger = logger
		self.wdt	= wdt
#		self.mqtt   = MQTTClient("umqtt_client", server=host, port=port, user=token, password="")
	def publish(self, telemetry, attributes, fromDB =False):
		try:
			print("Publicando en %s en %s" %(self.token, self.host,))
			response = requests.post("http://%s:%s/api/v1/%s/attributes" %(self.host,self.port,self.token), data = attributes, headers={"Content-Type": "application/json"})
			print("P.Atributes: %i" %response.status_code)
			response = requests.post("http://%s:%s/api/v1/%s/telemetry" %(self.host,self.port,self.token), data = telemetry, headers={"Content-Type": "application/json"})
			print("P.Telemetry: %i" %response.status_code)
			print(telemetry)
			if (response.status_code is not 200):
				raise Exception("Error %d en publicacion" %(response.status_code))	
			self.wdt.feed()
			return True	
#			self.mqtt.connect()
#			self.mqtt.publish(self.ATTRIBUTE_URL, attributes)
#			self.mqtt.publish(self.TELEMETRY_URL, telemetry)
#			self.mqtt.disconnect()
		except Exception as e:
			print("No fue posible publicar datos de %s en %s debido a: %s" %(self.token, self.host,repr(e)))
			self.logger.error("No fue posible publicar datos de %s en %s debido a: %s" %(self.token, self.host,repr(e)))
			self.wdt.feed()
#			self.logger.debug(repr(e))
#			print(repr(e))
			if (not fromDB):
				self.saveData(telemetry)
		return False

	def saveData(self,data):
		tel_offline=loads(data)
		if self.format == "complete":
			tel_offline["info-extra"] = "{'modo':'offline'}"
		tel_offline=dumps(tel_offline)
		self.logger.data(self.getDatalogFilename(), tel_offline)
		print("Datos %s guardados en archivo %s"%(self.format, self.getDatalogFilename()))
		
	def getDatalogFilename(self):
		return "datalog_%s"%self.token
		
	def dbPublish(self, attributes,uart, uart2, i2c, spi, logger, hpma_pin, pms_pin, publishers):
		if(not self.logger.readLinesCbk(self.getDatalogFilename(), lambda line: self.publish(line.strip('\r\n'), attributes, True),uart, uart2, i2c, spi, logger, hpma_pin, pms_pin, publishers, attributes)):
			print("Eliminando archivo %s" %self.getDatalogFilename())
			self.logger.removeFile(self.getDatalogFilename())
			try:
				self.logger.removeFile(self.getDatalogFilename()+"_idx")
			except Exception as e:
				pass
