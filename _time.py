from utime import localtime, time
import usocket as socket
from ustruct import unpack
from machine import RTC
# (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
NTP_DELTA = 3155673600

def ntime(host):
	NTP_QUERY = bytearray(48)
	NTP_QUERY[0] = 0x1b
	addr = socket.getaddrinfo(host, 123)[0][-1]
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.settimeout(1)
	res = s.sendto(NTP_QUERY, addr)
	msg = s.recv(48)
	s.close()
	val = unpack("!I", msg[40:44])[0]
	return val - NTP_DELTA

# There's currently no timezone support in MicroPython, so
# localtime() will return UTC time (as if it was .gmtime())
def settime(host = "ntp.shoa.cl"):
	t = ntime(host)
	tm = localtime(t)
	tm = tm[0:3] + (0,) + tm[3:6] + (0,)
	if tm[0]> 2019:
		RTC().datetime(tm)
		print("Reloj RTC sincronizado")
		return True
	else:
		return False

def now():
	fch=localtime()
#	return str(fch[0])+"-"+str(fch[1])+"-"+str(fch[2])+" "+str(fch[3])+":"+str(fch[4])+":"+str(fch[5])
	return "%s-%s-%s %s:%s:%s"%(fch[0],fch[1],fch[2],fch[3],fch[4],fch[5])

def setntp(logger = None):
	tact=time() #Tiempo actual
	print("Seteando reloj RTC...")
	timeout = time() + 5
	test = 1
	while True:
		try:
			print("Intento %i para sincronizar reloj mediante NTP" %test)
			if (test > 5 or time() > timeout or settime()):
				break
			test = test + 1
		except Exception as e:
			print(repr(e))
			if logger is not None:
				logger.error("Error al sincronizar el reloj mediante NTP",e)





