import utime
from ustruct import pack, unpack

class SPS30:
	_serial = None
	buf_start=[0x7e, 0x00, 0x00, 0x02, 0x01, 0x03, 0xf9, 0x7e]
	buf_stop=[0x7e, 0x00, 0x01, 0x00, 0xfe, 0x7e]
	buf_read=[0x7e, 0x00, 0x03, 0x00, 0xfc, 0x7e]
	buf_rst=[0x7e, 0x00, 0xD3, 0x00, 0x2c, 0x7e] #reset
	buf_PN=[0x7e, 0x00, 0xD0, 0x01, 0x01, 0x2D, 0x7e]# Product Name
	buf_AC=[0x7e, 0x00, 0xD0, 0x01, 0x02, 0x2C, 0x7e] # Article Code
	buf_SN=[0x7e, 0x00, 0xD0, 0x01, 0x03, 0x2B, 0x7e] #Serial number
	buf_SFC=[0x7e, 0x00, 0x56, 0x00, 0xa9, 0x7e] #Start Fan Cleaning
	

	def __init__(self, uart):
		self._serial = uart
		self._pm0p5Count = None
		self._pm1Count = None
		self._pm2p5Count = None
		self._pm4Count = None
		self._pm10Count = None
		self._pm1 = None
		self._pm2p5 = None
		self._pm4 = None
		self._pm10 = None
		
	def init(self):
		self._serial.write(bytearray(buf_rst))
		self.readme()
		utime.sleep(5)
		
	def CMD(self, cmd):
		comandos ={
			"0x0": "Start measurements",
			"0x1": "Stop measurements",
			"0x3": "Read measured value",
			"0x80": "Read/Write Auto Cleaning Interval",
			"0x56": "Start Fan Cleaning",
			"0xD0": "Device Information",
			"0xD3": "Reset",
			
		}
		print(comandos[str(hex(cmd))])
		
	def errorCode(self, estado):
		errores ={
			"0x0": "All good",
			"0x1": "Wrong data length for this command (too much or little data)",
			"0x2": "Unknown command",
			"0x3": "No access right for command",
			"0x4": "Illegal command parameter or parameter out of allowed range",
			"0x40": "Internal function argument out of range",
			"0x43": "Command not allowed in current state",
			"0x50": "No response received within timeout period",
			"0x51": "Protocol error",
			"0xff": "Unknown Error"
		}
		print(errores[str(hex(estado))])
	
	def calcFloat(self, data):
		#print(data)
		struct_float = pack('>BBBB', data[0], data[1], data[2], data[3])
		float_values = unpack('>f', struct_float)
		first = float_values[0]
		return first
		
	def readme(self):
		buff=[0]*50
		largo=0
		eval= 0
		print("Leyendo datos desde sensirion")
		while True:
			flag=ord(self._serial.read(1))
			#print(flag)
			if (flag== 0x7E):
				#print("bandera encontrada")
				if (ord(self._serial.read(1)) == 0):
					self.CMD(ord(self._serial.read(1)))
					self.errorCode(ord(self._serial.read(1)))
					largo=ord(self._serial.read(1)) #Leer largo de data
					print("largo de data: %x"%largo)
					j=0
					while(eval!=0x7E):
						buff[j]=ord(self._serial.read(1))
						eval=buff[j]
						#print (buff[j])
						#print(eval)
						#print(type(eval))
						j+= 1
					if(largo > 0):
						for i in range(j-3):
							if (buff[i]==0x7D):
								if (buff[i+1]==0x5E): buff[i]=0x7E
								if (buff[i+1]==0x5D): buff[i]=0x7D
								if (buff[i+1]==0x31): buff[i]=0x11
								if (buff[i+1]==0x33): buff[i]=0x13
								for k in range(i+1,j-4): buff[k] = buff[k+1]
						print("calcfloat")
						self._pm0p5Count = self.calcFloat(buff[16:20])
						self._pm1Count = self.calcFloat(buff[20:24])
						self._pm2p5Count = self.calcFloat(buff[24:28])
						self._pm4Count = self.calcFloat(buff[28:32])
						self._pm10Count = self.calcFloat(buff[32:36])
						self._pm1 = min(max(self.calcFloat(buff[0:4]), 0), 1000)
						self._pm2p5 = min(max(self.calcFloat(buff[4:8]), 0), 1000)
						self._pm4 = min(max(self.calcFloat(buff[8:12]), 0), 1000)
						self._pm10 = min(max(self.calcFloat(buff[12:16]), 0), 1000)
						return True
					else:
						print("ACK")
						return False
				else:
					print("Problemas con la lectura")
					return False
	
	def start(self):
		self._serial.write(bytearray(SPS30.buf_start))
		print("start")
		self.readme()
		
	def stop(self):
		self._serial.write(bytearray(SPS30.buf_stop))
		print("stop")
		self.readme()
		
	def measure(self):
		self._serial.write(bytearray(SPS30.buf_read))
		print("Measure")
		if(self.readme()):
			return True
		else:
			return False
		
	def reset(self):
		self._serial.write(bytearray(SPS30.buf_rst))
		print("Reset")
		self.readme()

	def clean(self):
		self._serial.write(bytearray(SPS30.buf_SFC))
		print("Clean fan")
		self.readme()

		
	