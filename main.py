import sensorpool
from logger_ import Logger
from publisher_ import Publisher
import _time #as _time
import config #as config
from sys import print_exception
from os import getcwd
from ujson import dumps
from utime import sleep, time, ticks_ms
from machine import UART,I2C ,Pin, deepsleep, wake_reason, SPI, WDT, freq#, Timer, disable_irq, enable_irq
from esp32 import raw_temperature

VERSIONSW 	= "2.4.2.2"
TAIRF 		= 12
TSTAMP 		= 946684800
LOGDAT 		= 'logdata.txt'
amok 		= 0
hmok 		= 0
pmok 		= 0

print(getcwd())

def readandpublish(timer,uart, uart2, i2c, spi, logger, hpma_pin, pms_pin, publishers, atrpub):
	# Inicia sensores
	sensors = sensorpool.startSensors(uart = uart, uart2 = uart2, i2c = i2c, spi = spi, logger = logger, hpma_pin=hpma_pin, pms_pin=pms_pin)
	print('Flujo de aire forzado por %d segundos...' %TAIRF)
	sleep(TAIRF)
	print('Realizando medicion...')
	measures=sensorpool.readsensors(sensors, logger)
	
	# Apaga sensores de material particulado
	hpma_pin.value(0)
	pms_pin.value(0)
	
	## **************** PREPARACIÓN DE PAQUETES DE TELEMETRÍA **************** 
	tstp	= (time()+TSTAMP)*1000
	fecha	= _time.now()
	
	print("PM2.5: %.2f %.2f %.2f ug/m3 [H-P-S]" % (measures["HPM2_5"], measures["PPM2_5"], measures["SPM2_5"]))
	print("PM10:  %.2f %.2f %.2f ug/m3 [H-P-S]" % (measures["HPM10"], measures["PPM10"], measures["SPM10"]))
	print("Temperatura: %.2f ºC" %(measures["Temp"]))
	print("Humedad Rel: %.2f %%" %(measures["HR"]))
	
	# Finaliza ina219
	sensors["ina219"].stop()
	sensors["ina219"].join()
	
	simple_tel = {}
	simple_tel["tiempo"]= fecha
	simple_tel["tesp"]	= (raw_temperature()-32)*0.5555556
	simple_tel["hmok"]	= int("hpma115s0" in sensors)
	simple_tel["pmok"]	= int("pms7003" in sensors)
	simple_tel["amok"]	= int("am2315" in sensors or "am2302" in sensors)
	simple_tel["spok"]	= int("sps30" in sensors)

	complete_tel 		= config.measurements()
	complete_tel["tesp"]["medicion:otro:temperatura"]			= (raw_temperature()-32)*0.5555556
#	complete_tel["tesp"]["tipo"]								= "meteorologia:temperatura:\xbaC"
	complete_tel["tesp"]["fecha:otro:temperatura"]				= tstp
		
	pub_tel = {}
	pub_tel["tesp"]=complete_tel["tesp"]
	
	if "hpma115s0" in sensors: 	
		pub_tel["hm2_5"]											= complete_tel["hm2_5"]
		pub_tel["hm10"]												= complete_tel["hm10"]
		simple_tel["HPM2.5"] 										= measures["HPM2_5"]
		simple_tel["HPM10"] 										= measures["HPM10"]
		complete_tel["hm10"]["medicion:contaminante:mp10"]			= measures["HPM10"]
		complete_tel["hm10"]["fecha:contaminante:mp10"]				= tstp
		complete_tel["hm2_5"]["medicion:contaminante:mp2_5"]		= measures["HPM2_5"]
		complete_tel["hm2_5"]["fecha:contaminante:mp2_5"]			= tstp
		
	if "pms7003" in sensors:
		pub_tel["pm2_5"]											= complete_tel["pm2_5"]
		pub_tel["pm10"]												= complete_tel["pm10"]
		simple_tel["PPM2.5"] 										= measures["PPM2_5"]
		simple_tel["PPM10"] 										= measures["PPM10"]
		complete_tel["pm10"]["medicion:contaminante:mp10"]			= measures["PPM10"]
		complete_tel["pm10"]["fecha:contaminante:mp10"]				= tstp
		complete_tel["pm2_5"]["medicion:contaminante:mp2_5"]		= measures["PPM2_5"]
		complete_tel["pm2_5"]["fecha:contaminante:mp2_5"]			= tstp

	if "am2315" in sensors or "am2302" in sensors:
		pub_tel["temp"]												= complete_tel["temp"]
		pub_tel["hur"]												= complete_tel["hur"]	
		simple_tel["Temp"] 											= measures["Temp"]
		simple_tel["HR"] 											= measures["HR"]
		complete_tel["temp"]["medicion:meteorologia:temperatura"]	= measures["Temp"]
		complete_tel["temp"]["fecha:meteorologia:temperatura"]		= tstp
#		complete_tel["temp"]["tipo"]								= "meteorologia:temperatura:\xbaC"
		complete_tel["hur"]["medicion:meteorologia:humedad"]		= measures["HR"]
		complete_tel["hur"]["fecha:meteorologia:humedad"]			= tstp
		
	if "sps30" in sensors:
		pub_tel["sm2_5"]											= complete_tel["sm2_5"]
		pub_tel["sm10"]												= complete_tel["sm10"]
		simple_tel["SPM2_5"]										= measures["SPM2_5"]
		simple_tel["SPM10"]											= measures["SPM10"]
		complete_tel["sm10"]["medicion:contaminante:mp10"]			= measures["SPM10"]
		complete_tel["sm10"]["fecha:contaminante:mp10"]				= tstp
		complete_tel["sm2_5"]["medicion:contaminante:mp2_5"]		= measures["SPM2_5"]
		complete_tel["sm2_5"]["fecha:contaminante:mp2_5"]			= tstp
		
	if "ina219" in sensors and sensors["ina219"].voltage is not None:
		simple_tel["voltage"] 										= sensors["ina219"].voltage
		simple_tel["current"]									 	= sensors["ina219"].current
		simple_tel["power"] 										= sensors["ina219"].power
		complete_tel["voltage"]["medicion:otro:voltaje"]			= sensors["ina219"].voltage
		complete_tel["voltage"]["fecha:otro:voltaje"]				= tstp
		complete_tel["current"]["medicion:otro:corriente"]			= sensors["ina219"].current
		complete_tel["current"]["fecha:otro:corriente"]				= tstp
		complete_tel["power"]["medicion:otro:potencia"]				= sensors["ina219"].power
		complete_tel["power"]["fecha:otro:potencia"]				= tstp
		pub_tel["voltage"]											= complete_tel["voltage"]
		pub_tel["current"]											= complete_tel["current"]	
		pub_tel["power"]											= complete_tel["power"]	
	
	simple_tel = {
		"ts": tstp,
		"values": simple_tel
	}

	## **************** PUBLICACIÓN DE TELEMETRIAS **************** 

	for pub in publishers:
		try:
			if pub.format == "simple":
				print("\nPublica simple: %s"%dumps(simple_tel))
				pub.publish(dumps(simple_tel), atrpub)
			elif pub.format == "complete":
				for meas in pub_tel:
					print("\nPublica completo: %s"%dumps(pub_tel[meas]))
					pub.publish(dumps(pub_tel[meas]), atrpub)
			
		except Exception as e:
			print_exception(e)	
			print(repr(e))
			logger.debug("Error en la publicación")
			logger.debug(print_exception(e))

	logger.data(LOGDAT, dumps(simple_tel))

def start(wdt=None):
	freq(80000000)
#	timer = Timer(2)
	print("iniciando...")
	print(wake_reason())
	if wdt is None:
		wdt = WDT(timeout=240000)
	# Inicializa habilitación de los sensores de material particulado.
	hpma_pin 	= Pin(16, Pin.OUT) #Se?al de activaci?n de transistor
	pms_pin 	= Pin(4, Pin.OUT) #Se?al de activaci?n de transistor
#	hpma_pin.value(0)
#	pms_pin.value(0)

	# Configura buses de comunicación.
	uart 	= UART(2, baudrate=115200, rx=32, tx=17, timeout=1000)
	uart2	= UART(1, baudrate=9600, rx=33, tx=2, timeout=1000)
	i2c 	= I2C(sda = Pin(21, Pin.PULL_UP), scl = Pin(22,Pin.PULL_UP), freq = 20000)
	spi 	= SPI(sck = Pin(14), mosi = Pin(13), miso = Pin(15))
	cs 		= Pin(5, Pin.OUT)

	# Inicia logger. Interfaz para SD.
	logger = Logger(spi = spi, cs = cs)
	logger.success("Estacion inicializada")
	# Sincroniza NTP
	_time.setntp(logger = logger)

	#Crea publicadores
	publishers = []
	for pub in config.publishers(logger):
		publishers.append(
			Publisher(host = pub["host"], token = pub["token"], port = pub["port"], format_ = pub["format"], logger = logger, wdt=wdt)
		)
	attr 				= config.attributes()
	attr["version"]		= VERSIONSW
	atrpub				= dumps(attr)
#	print("iniciando timer")
#	timer.init(period=540000, mode=Timer.PERIODIC, callback=lambda t:readandpublish(None,uart, uart2, i2c, spi, logger, hpma_pin, pms_pin, publishers, atrpub))
#	print("timer iniciado")
	readandpublish(None, uart, uart2, i2c, spi, logger, hpma_pin, pms_pin, publishers, atrpub)
	# Vuelve a intentar insertar las telemetrias pendientes desde la bd
	freq(240000000)
	for pub in publishers:
		pub.dbPublish(atrpub,uart, uart2, i2c, spi, logger, hpma_pin, pms_pin, publishers)
	logger.success("Ciclo de funcionamiento exitoso")
	logger.close()
#	state = disable_irq()
#	timer.deinit()
	return
#		print('Sensor y ESP32 en modo sleep')
#		break
#		twking=utime.ticks_ms()
#		deepsleep(600000-twking)#10 minutos
	#	deepsleep(20000) #20 segundos

if __name__ == '__main__':
	start()
	twking=ticks_ms()
	print('ESP32 in deep sleep by %d msecs' %(600000-twking))
	deepsleep(600000-twking)#10 minutos