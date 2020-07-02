from ina219_ import INA219_
import lib.sps30 as sps30
import lib.hpma2 as hpma2
from lib.pms7003 import PMS7003
from lib.am2315 import *
import _thread
from utime import sleep, time as timee
from dht import DHT22
from sys import print_exception
from machine import Pin, UART

def startSPS30(num, sensors, uart,pin,logger=None):
	try:
		print("Inicializando SPS30-%d..."%num)
		pin.value(1)
		sleep(0.3)
		sps=sps30.SPS30(uart)
		sleep(0.2)
		sps.start()
		sleep(2)
		if(sps.measure()):
			sps.clean()
			print("SPS30-%d inicializado" %num)
			logger.success("Sensor SPS30-%d inicializado" %num)
			if num is 2:
				sensors["sps30-"+str(num)] = sps
			else:
				sensors["sps30"] = sps
			return sensors
	except Exception as e:
		print_exception(e)	
		print("No se pudo iniciar SPS30")
		pin.value(0)
		print(repr(e))
		sleep(0.5)
		return sensors
		
def startHPMA115S0(num, sensors, uart, pin,logger=None):
	print("Iniciando sensor HPMA115S0")
	tmout = timee() + 15   # 15 segundos
	test = 0
	hmok = 0
	while hmok == 0:
		pin.value(1)
		try:
			hpma = hpma2.HPMA115S0(uart)
			hpma.init()
			hpma.startParticleMeasurement()
			if (hpma.readParticleMeasurement()):
				# hmok = 1
				print("HPMA115S0-%d inicializado" %num)
				logger.success("HPMA115S0-%d inicializado" %num)
				if not "hpma115s0" in sensors:
					sensors["hpma115s0"] = hpma
				else:
					sensors["hpma115s0-2"] = hpma
				break
		except Exception as e:
			print(repr(e))
		if (test > 15 or timee() > tmout):
			print("No se pudo iniciar HPMA115S0")
			pin.value(0)
			sleep(0.5)
			break
		test += 1
	return sensors

def startSensors(uart = None, uart2 = None, i2c = None, spi = None, logger = None, hpma_pin=None, pms_pin=None, **kwargs):

	sensors = dict()

#	hpma_pin 	= Pin(16, Pin.OUT) #Se?al de activaci?n de transistor
	# pms_pin 	= Pin(4, Pin.OUT) #Se?al de activaci?n de transistor

	# Inicia sensor PMS7003

	try:
		pms_pin.value(1)
		pms = PMS7003(uart2)
		if(pms.init()):
			pmok=1
			sensors["pms7003"] = pms
			logger.success("Sensor PMS7003 inicializado")
	except Exception as e:
		print(repr(e))
		pms_pin.value(0)

	if not uart is None:
		sensors=startSPS30(1,sensors,uart,hpma_pin,logger)

	if not "sps30" in sensors:
		
		uart.deinit()
		uart 	= UART(2, baudrate=9600, rx=32, tx=17, timeout=1000)
		sensors	=startHPMA115S0(1, sensors,uart, hpma_pin,logger)

	if not "pms7003" in sensors and not "am2315" in sensors:
		print("iniciando AM2302")
		tmout = timee() + 2   # 2 segundos
		test = 0
		while True:
			try:
#			am2302_pin	= Pin(4, Pin.OUT) #Senal de activaci?n de transistor
				pms_pin.value(1)
				sleep(0.1)
				am2302 = DHT22(Pin(2))
				am2302.measure()
				sensors["am2302"] = am2302
#			print(sensors["am2302"].humidity())
#			print(sensors["am2302"].temperature())
				print("Sensor AM2302 inicializado")
				logger.success("Sensor AM2302 inicializado")
				break
			except Exception as e:
#					sys.print_exception(e)	
				print(repr(e))
			if (test == 3 or timee() > tmout):
				print("No se pudo iniciar AM2302")
				del am2302
				pms_pin.value(0)
#				sleep(0.5)
				break
			test = test + 1
#			pms_pin.value(0)
			sleep(0.5)

	if not i2c is None:
		# Inicia sensor AM2315
		tmout = timee() + 5   # 5 segundos
		test = 0
		while True:
			try:
				am2315 = AM2315( i2c = i2c )
				print("Iniciando sensor AM2315...")
				if(am2315.measure()):
					print("AM2315 inicializado")
					logger.success("Sensor AM2315 inicializado")
					sensors["am2315"] = am2315	
					break
			except Exception as e:
				print_exception(e)	
				print("No se pudo iniciar AM2315")
				print(repr(e))
				
			if (test == 5 or timee() > tmout):
				print("No se pudo iniciar AM2315")
				break
			test = test + 1
		
		try:
			# Inicia sensor INA219
			#Crea hilo para lectura del sensor am2315
			ina219 = INA219_(buffLen = 3, period = 5, sem = None, on_read = None, **kwargs)
			#Comienza lectura del sensor
			_thread.start_new_thread(ina219.run, ())
			sensors["ina219"] = ina219
		except Exception as e:
			print_exception(e)	
			print("No se pudo iniciar INA219")
			print(repr(e))

	if not spi is None:
		pass

	if not "am2302" in sensors and not "sps30-2" in sensors and not "pms7003" in sensors:
		try:
			uart2.deinit()
		except Exception as e:
			pass
		uart2 	= UART(1, baudrate=9600, rx=33, tx=2, timeout=1000)
		sensors=startHPMA115S0(2, sensors,uart2, pms_pin)
		
	return sensors
	
def readsensors(sensors, logger):
	HPM2_5,HPM10, PPM2_5, PPM10, tem, hr, SPM2_5, SPM10 =([0.0]*5,[0.0]*5,[0.0]*5,[0.0]*5,[0.0]*5,[0.0]*5,[0.0]*5,[0.0]*5)

	# Lectura de los sensores. 5 mediciones
	for i in range(5):
		try:
#		# Lee HPMA115S0
			if "hpma115s0" in sensors: 
				sensors["hpma115s0"].readParticleMeasurement()
				HPM2_5[i]	= sensors["hpma115s0"]._pm2_5
				HPM10[i]	= sensors["hpma115s0"]._pm10
		except Exception as e:
			print_exception(e)	
			print(repr(e))
			logger.warning("Error en lectura de sensor honeywell",e)
		try:
			if "pms7003" in sensors:
#						# Lee PMS7003
				pms_data 	= sensors["pms7003"].read()
				PPM2_5[i]	= min(max(pms_data['PM2_5'], 0), 1000)
				PPM10[i]	= min(max(pms_data['PM10_0'], 0), 1000)
		except Exception as e:
			print_exception(e)	
			print(repr(e))
			logger.warning("Error en lectura de sensor plantower",e)
		try:
			# Lee AM2315
			if "am2315" in sensors:
				sensors["am2315"].measure()
				tem[i]		= sensors["am2315"].temperature()
				hr[i]		= sensors["am2315"].humidity()
		except Exception as e:
			print_exception(e)	
			print(repr(e))
			logger.warning("Error en lectura de sensor AM2315",e)
		try:
			if "am2302" in sensors:
				sensors["am2302"].measure()
				tem[i]		= sensors["am2302"].temperature()
				hr[i]		= sensors["am2302"].humidity()
		except Exception as e:
			print_exception(e)	
			print(repr(e))
			logger.warning("Error en lectura de sensor AM2302",e)
		try:
			if "sps30" in sensors:
				sensors["sps30"].measure()
				SPM2_5[i]		= sensors["sps30"]._pm2p5
				SPM10[i]		= sensors["sps30"]._pm10
		except Exception as e:
			print_exception(e)	
			print(repr(e))
			logger.warning("Error en lectura de sensor SPS30",e)
		
	HPM2_5	= list(sorted(HPM2_5))
	HPM10	= list(sorted(HPM10))
	PPM10	= list(sorted(PPM10))
	PPM2_5	= list(sorted(PPM2_5))
	tem		= list(sorted(tem))
	hr		= list(sorted(hr))
	SPM2_5	= list(sorted(SPM2_5))
	SPM10	= list(sorted(SPM10))
	measures = {}
#	if "hpma115s0" in sensors: 	
	measures["HPM2_5"] 	= HPM2_5[2]
	measures["HPM10"] 	= HPM10[2]
#	if "pms7003" in sensors:
	measures["PPM2_5"] 	= PPM2_5[2]
	measures["PPM10"] 	= PPM10[2]			
#	if "am2315" in sensors or "am2302" in sensors:
	measures["Temp"] 	= tem[2]
	measures["HR"] 		= hr[2]			
#	if "sps30" in sensors:
	measures["SPM2_5"]	= SPM2_5[2]
	measures["SPM10"]	= SPM10[2]
#	if "ina219" in sensors and sensors["ina219"].voltage is not None:
	measures["voltage"]	= sensors["ina219"].voltage
	measures["current"]	= sensors["ina219"].current
	measures["power"] 	= sensors["ina219"].power
	if "sps30" in sensors and SPM2_5[2]==1000:
		logger.warning("Sensor de material particulado saturado")
	if "ina219" in sensors and measures["voltage"] <= 3.3:
		logger.warning("Bateria baja %s V" %measures["voltage"])
		print("Bateria baja")
	return measures
		