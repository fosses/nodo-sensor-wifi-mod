#!/usr/bin/env python3
# -*- coding: utf-8 -*-

## @file ina219_.py
# @brief Contiene clase con funciones para monitoreo del sensor ina219 usando esquema multihilo en base a una librería de github.
# @see https://github.com/chrisb2/pi_ina219/
# @see config/config.py
# @see services/sensor.py
from lib.ina219 import INA219
from lib.ina219 import DeviceRangeError
from sensor import Sensor
import _time
import time, _thread
from ucollections import deque
from machine import I2C, Pin
from lib import stats


## @class INA219_
# @code{.py}
# @endcode
class INA219_(Sensor):
    ## Nombre del sensor.
    name                = "ina219"
    ## Resistencia shunt en ohms del sensor.
    SHUNT_OHMS          = 0.1
    ## Cantidad máxima de miliamperes que se esperan que pasen por el sensor.
    MAX_EXPECTED_AMPS   = 700

    ## @brief Constructor de la clase.
    # @param[in] buffLen Tamaño del buffer de mediciones.\n
    # @param[in] period Periodo de tiempo entre mediciones.\n
    # @param[in] sem Semáforo i2c para evitar conflictos.\n
    # @param[in] on_read Callback a llamar cada vez que se llenan los buffers de mediciones.\n
    # @param[in] nattempts Cantidad de reintentos de lectura por medición.\n
    # @param[in] maxTimeOffset Máximo tiempo de offset entre que termina un período de mediciones y comienza el siguiente.\n
    # @param[in] kwargs Diccionario con parámetros de entrada para función callback.
    def __init__(self, buffLen = 11, period = 60, sem = None, on_read = None, nattempts = 3, maxTimeOffset = 15,  **kwargs):
        ## Tamaño del buffer de mediciones
        self.buffLen        = buffLen                       
        ## Periodo de tiempo entre mediciones
        self.period         = period                        
        ## Semáforo i2c para evitar conflictos
        self.semI2C         = sem                           
        ## Buffer de mediciones de voltaje
        self.voltBuff       = None                          
        ## Buffer de mediciones de corriente
        self.currBuff       = None                 
        ## Callback a llamar cada vez que se llenan los buffers de mediciones
        self.on_read        = on_read                       
        ## Argumentos extra a pasar a la función callback
        self.kwargs         = kwargs                        
        ## Cantidad de intentos de lectura por medición
        self.nattempts      = nattempts                     
        ## Último valor de voltaje
        self.voltage        = None                          
        ## Último valor de corriente
        self.current        = None                          
        ## Último valor de potencia
        self.power       = None                          
        ## Cantidad máxima de tiempo extra que puede tardar en tomar todas las muestras
        self.maxTimeOffset 	= maxTimeOffset                 

        #Inicializa hilo
        Sensor.__init__(self)
    
    ## @brief Adquiere control del bus I2C
    def startI2CCritical(self):
        if not self.semI2C is None:
            self.semI2C.acquire()
    
    ## @brief Libera control del bus I2C
    def stopI2CCritical(self):
        if not self.semI2C is None:
            self.semI2C.release()
    
    ## @brief Rutina del sensor
    def run(self):
        #Activa flag para saber que el hilo se está ejecutando
        self.startSensor()

        while True:
            #Marca tiempo de inicio
            st = time.time()
            while True and not self.isStopping():
                #Inicializa buffers
                ## Buffer de mediciones de voltaje en V.
                self.voltBuff   = []
                ## Buffer de mediciones de corriente en mA.
                self.currBuff   = []
                ## Buffer de mediciones de potencia en mW.
                self.powBuff    = []
                
                for i in range(self.buffLen):

                    if time.time()-st > self.period*self.buffLen + self.maxTimeOffset:
                        #Salta timeout por finalización de tiempo estipulado para muestreo
                        break

                    #Duerme hasta que sea necesario muestrear
                    if time.time()-st <self.period*(i+1):
                        time.sleep(self.period*(i+1)-(time.time()-st))
                    
                    self.startCritical()

                    #Pide recurso I2C
                    self.startI2CCritical()

                    #Vuelve a crear objeto. Al parecer debe hacerse luego de encenderlo.
                    for attempt in range(3):
                        try:
                            ## Objeto INA219 de la librería Adafruit.
                            # self.ina219         = INA219(INA219_.SHUNT_OHMS, INA219_.MAX_EXPECTED_AMPS)
                            # self.ina219.configure(bus_adc = INA219.ADC_64SAMP, shunt_adc = INA219.ADC_64SAMP)
                            self.ina219 = INA219(INA219_.SHUNT_OHMS, I2C(-1, Pin(22), Pin(21)))
                            self.ina219.configure()
                            break
                        except Exception as e:
                            print("Error al crear objeto INA219")
                            time.sleep(0.1)

                    #Inicializa cantidad de intentos realizados
                    attempt = 1

                    while attempt <= self.nattempts:
                        try:
                            #Realiza lectura de corriente, voltaje y potencia
                            self.voltBuff.append(self.ina219.voltage())
                            self.currBuff.append(self.ina219.current())
                            self.powBuff.append(self.ina219.power())
                            break
                        except:
                            print("Error al leer sensor ina219")

                            #Actualiza contador de intentos
                            attempt += 1

                            #Duerme un segundo hasta el siguiente intento
                            time.sleep(1)

                    #Libera recurso I2C
                    self.stopI2CCritical()

                    #Libera control del hilo
                    self.stopCritical()

                    #Muestra por pantalla los valores obbtenidos
                    if len(self.voltBuff)>0 and len(self.currBuff)>0 and len(self.powBuff)>0:
                        print("INA219 %s: Voltaje: %.2f. Corriente: %.2f. Potencia: %.2f"%(_time.now(), self.voltBuff[-1], self.currBuff[-1], self.powBuff[-1]))
                
                #Adquiere control del hilo
                self.startCritical()

                #Actualiza última medición de corriente
                if len(self.currBuff)>0:
                    ## Último valor de corriente extraido de la mediana del último buffer de mediciones de corriente.
                    self.current    = stats.median(list(sorted(self.currBuff)))
                
                #Actualiza última medición de voltaje
                if len(self.voltBuff)>0:
                    ## Último valor de voltaje extraido de la mediana del último buffer de mediciones de voltaje.
                    self.voltage    = stats.median(list(sorted(self.voltBuff)))

                #Actualiza última medición de potencia
                if len(self.powBuff)>0:
                    ## Último valor de potencia extraido de la mediana del último buffer de mediciones de potencia.
                    self.power      = stats.median(list(sorted(self.powBuff)))

                if not self.on_read is None:
                    #Llama callback para procesamiento de los datos
                    self.on_read(self, **self.kwargs)
                
                #Libera control del hilo
                self.stopCritical()

                #Actualiza tiempo inicial
                st = st + self.buffLen*self.period

                #Espera a siguiente período de muestreo
                if(time.time() < st):
                    time.sleep(st-time.time())
            #Avisa que ha terminado de ejecutarse el hilo
            self.endSensor()

            #Espera a que se requiera nuevamente la ejecución del hilo
            self.waitForActivation()
if __name__ == '__main__':
    def publish_loop(**kwargs):
        q = kwargs["queue"]
        while True:
            while True:
                try:
                    telemetry = q.popleft()
                    break
                except:
                    pass
                time.sleep(5)
                print("esperando publicar..")
            print(telemetry)
    def onRead(sensorObj, **kwargs):
        q = kwargs["queue"]
        telemetry = {
            "voltage": sensorObj.voltage,
            "current": sensorObj.current,
            "power": sensorObj.power
        }
        d.append(telemetry)
        print("Bus Voltage: %.3f V" % sensorObj.voltage)
        print("Current: %.3f mA" % sensorObj.current)
        print("Power: %.3f mW" % sensorObj.power)
    
    d = deque((), 11)
    kwargs = {
        "queue": d
    }

    #Crea hilo para lectura del sensor am2315
    ina219 = INA219_(buffLen = 3, period = 5, sem = None, on_read = onRead, **kwargs)
    #Comienza lectura del sensor
    _thread.start_new_thread(ina219.run, ())
    _thread.start_new_thread(lambda: publish_loop(**kwargs), ())

    time.sleep(17)

    ina219.stop() # Detiene el sensor
    ina219.join() # Espera a que el sensor se detenga
    #ina219.start()