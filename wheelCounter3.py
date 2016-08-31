import serial
import time
import pigpio
import math

# for gpsd
import os
from gps import *
import threading

gpsd = None #setting the global variable

class GpsPoller(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    global gpsd #bring it in scope
    gpsd = gps(mode=WATCH_ENABLE) #starting the stream of info
    self.current_value = None
    self.running = True #setting the thread running to true
 
  def run(self):
    global gpsd
    while self.running:
      gpsd.next() #this will continue to loop and grab EACH set of gpsd info to clear the buffer
	  
class IMU:
	def __init__ (self,portName, imuNum, baud):
		self.port = portName
		self.imu = serial.Serial ( portName, baud, timeout=None )
		self.imuNum = imuNum
		
	def readLine ( self ):
		#self.tmString = time.strftime ( "%H%M%S" ) 
		imuData = self.imu.readline( )
		return imuData 

class Wheel:

	def __init__ ( self, pi, gpioPin ) :
		self.spokeCounter = 0 
		#cb = pi.callback( gpioPin, pigpio.FALLING_EDGE, self.wheelCounterCallback )
		#cb = pi.callback( gpioPin, pigpio.EITHER_EDGE, self.wheelCounterCallback )
		cb = pi.callback( gpioPin, pigpio.RISING_EDGE, self.wheelCounterCallback )
		
	def wheelCounterCallback( self, gpio, level,tick):
		#print ( "cb," + str(level) + "," + str(tick) ) ;
		#global wheelStatus
		
		self.spokeCounter = self.spokeCounter + 1
		#wheelStatus = "," + str(level) + "," + str(tick) ;

def main ( ) :

	# Start polling the gps
	gpsp = GpsPoller() # create the thread
	try:
		gpsp.start() # start it up

		# Open the log file with a unique name
		tmString = time.strftime ( "%Y%m%d-%H%M%S" )
		fname = 'F' + tmString + '.csv'
		f = open(fname, 'w')
		
		# Connect to pigpio server
		gpio = pigpio.pi()		# Use default host, port

		# Instantiate the wheel counters
		# WARNING: 
		# Per hardware, should be:
		# left wheel, gray wire, pin 24
		# right wheel, yellow wire, pin 23
		left = Wheel ( gpio, 23 )
		right = Wheel ( gpio, 24 )
		start = int(round(time.time() * 1000))
		
		# Instantiate the IMU
		imu = IMU ( "/dev/ttyUSB0", 1, 115200)
		
		# Write header line
		#f.write ( 'pi_time,leftWheelCount,rightWheelCount,lat,long,speed,track,gps_time,imu_time,N..,N.,N,E..,E.,E,GyroX,GyroY,GyroZ,AccelX,AccelY,AccelZ\n' )
		f.write ( 'pi_time,leftWheelCount,rightWheelCount,lat,long,speed,track,gps_time,yaw,pitch,roll,magX,magY,magZ,AccelX,AccelY,AccelZ,GyroX,GyroY,GyroZ\n' )
		
		# main loop
		while True:
			#print ( "mills b4=" + str (mills ) )
			mills = int(round(time.time() * 1000)) - start
			#start = int(round(time.time() * 1000))
			dataStr = str ( mills ) + ','
			dataStr = dataStr + str ( left.spokeCounter) + ','
			dataStr = dataStr + str ( right.spokeCounter) + ','
			dataStr = dataStr + str ( gpsd.fix.latitude) + ','
			dataStr = dataStr + str ( gpsd.fix.longitude) + ','
			dataStr = dataStr + str ( gpsd.fix.speed) + ','
			dataStr = dataStr + str ( gpsd.fix.track) + ','
			dataStr = dataStr + str ( gpsd.utc) +  ' ' + str ( gpsd.fix.time ) 
			dataStr = dataStr + ',' + str(imu.readLine ( ).rstrip ( ))
			#print ( "mills after=" + str (mills ) )
			f.write ( dataStr + '\n' )
			#print ( dataStr )
			#time.sleep ( 0.1 )
		close(f)	
	
	except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
		print "\nKilling Thread..."
		gpsp.running = False
		gpsp.join() # wait for the thread to finish what it's doing
	print "Done.\nExiting."
	
if __name__ == "__main__":
	main ( )
