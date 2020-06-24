#!/usr/bin/env python3
# -*- coding: utf-8 -*-

## @file sensor.py
# @brief Funcionalidades para los sensores de manera genérica. Contiene la clase Sensor, que hereda de Thread, la cual es usada como padre para todos los sensores, estableciendo un esquema multihilo. Se define una función callback para las mediciones de todos los sensores.
# @see config/config.py

import time, _thread

## @class Sensor
# @brief Esta clase hereda de Thread. Es utilizada como padre por todos los sensores. Establece funcionalidades básicas para los sensores, permitiendo la pausa y la reanudación.
class Sensor():
    ## @brief Constructor de la clase
    def __init__(self):
        ## Semáforo para acceder a recursos del hilo desde afuera
        self.runSem     = _thread.allocate_lock()        
        ## Flag para saber si está ejecutandose
        self.running 	= False			                
        ## Flag para saber si se está deteniendo
        self.stopping 	= False			                
    
    ## @brief Establece que el hilo ha comenzado a ejecutarse
    def startSensor(self):
        #Adquiere control del hilo
        self.startCritical()

        #Actualiza estado del sensor
        self.running = True

        #Libera control del hilo
        self.stopCritical()
    
    ## @brief Establece que el hilo se ha detenido
    def endSensor(self):
        #Adquiere control del hilo
        self.startCritical()

        #Actualiza estado del sensor
        self.stopping 	= False
        self.running 	= False

        #Libera control del hilo
        self.stopCritical()
    
    ## @brief Espera a que el hilo reanude su ejecución
    def waitForActivation(self):
        #Espera a que se requiera la ejecución del hilo
        while(not self.isRunning()):
            time.sleep(1)
    
    ## @brief Ordena detener el hilo en el próximo ciclo.
    def stop(self):
        #Adquiere control del hilo
        self.startCritical()

        self.stopping = True

        #Libera control del hilo
        self.stopCritical()
    
    ## @brief Pregunta si el hilo se está deteniendo
    #
    # @params[out] stopping Bandera que indica si el hilo se está deteniendo
    def isStopping(self):
        return self.stopping
    
    ## @brief Pregunta si el hilo está ejecutandose
    #
    # @params[out] running Bandera que indica si el hilo se está ejecutando
    def isRunning(self):
        return self.running

    ## @brief Adquiere control del hilo mediante un semáforo
    def startCritical(self):
        self.runSem.acquire()
    
    ## @brief Libera control del hilo mediante un semáforo
    def stopCritical(self):
        self.runSem.release()
    
    ## @brief Ordena reanudar el hilo en el próximo ciclo.
    def resume(self):
        #Adquiere control del hilo
        self.startCritical()

        self.running = True

        #Libera control del hilo
        self.stopCritical()
    
    def join(self):
        while(self.isRunning()):
            time.sleep(1)
