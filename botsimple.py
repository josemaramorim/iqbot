import time, json, collections

from iqoptionapi.stable_api import IQ_Option
from datetime import datetime
from dateutil import tz

#CREDENTIALS 
email = 'juandesndr@gmail.com'
password = 'juandesn38'
api = IQ_Option(email,password) #define API to a variable.

#VARIABLES
MAXSIZE = 3						#define number of coincidences (should be -1 than expected)
d = dict()						#define dictionary to save candles
expirations_mode = 1	    	#reference: https://github.com/Lu-Yi-Hsun/iqoptionapi/issues/6
CurrencyPair = "EURUSD-OTC"			#define pair to trade for example EURUSD or EURUSD-OTC
candleTime = 60					#define candle timeframe in SECONDS
BetAmount = 100					#define initial bet amount in USD
coeficient = 0.0				#coeficient to multiply when operation is loose
minCoeficient = 0.8				#Minimum coeficient to operate
candleId = 00000000				#Indentifier to check if win/loose and do for bucle trought dictionary 
status = 'L'					#status of operation W is won / T is tie / L is lost
direction = ''					#higher 'call' / #lower = 'put'
maxOperations = 10				#Max number of operations that can be done 
tryOperation = 1				#number of try to win. 
estimatedEarning = BetAmount * coeficient   #Estimated Earning to calcualte Asgale 
executeLoop = True				#Setted to true to get inside the loop and restart after winned Operation.
operationNumber = 0 			#Number of operation 

#FUNCTIONS
def loggin(): 					#Connect to IQ Option
	api.connect()	

def setMode(mode): 				#Define mode: PRACTICE/REAL
	api.change_balance(mode)	

def getServerTime():			#Get time synced with Server Clock
	while True:
		serverClock = api.get_server_timestamp()
		return (timestamp_converter(serverClock))
	
def getBalance(): 				#Get account balance
	balance = api.get_balance()
	print('Balance: '+str(balance))
	return balance
	
def getCurrency(): 				#Get Currency
	currency = api.get_currency()
	return currency

def setCoeficient():			#Define Coefficient
	global coeficient
	dprofit=api.get_all_profit()
	coeficient = dprofit[CurrencyPair]['turbo'] 
	print('Coefficient: '+str(coeficient))

def resetValues():				#Reset all bot values
	global counter
	global d
	global status
	global BetAmount
	global tryOperation

	counter = 0 		#reset counter to zero
	d.clear()			#reset dictionary to empty
	status = 'L'      	#reset status to Initial Value
	BetAmount = 100  	#reset bet amount to 1 
	tryOperation = 1	#reset try to 1
	setCoeficient()		#reset coeficient 
	stopStream()		#stop Stream
	startStream()		#reStart Stream
	
def getCandle():  				#Get the candle value (PAR, TIMEFRAME, HOW MANY CANDLES, TIME)
	candles = api.get_candles(CurrencyPair,candleTime,1,time.time())
	return candles

def startStream():				#Open candles stream
	api.start_candles_stream(CurrencyPair,candleTime,1) #(EURUSD,60,5)

def stopStream():				#Close candles stream
	api.stop_candles_stream(CurrencyPair,candleTime)	#(EUR,60)

def timestamp_converter(x): 	#Timeconverter
	hora = datetime.strptime(datetime.utcfromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S'),'%Y-%m-%d %H:%M:%S')
	hora = hora.replace(tzinfo=tz.gettz('GMT'))
	return str(hora.astimezone(tz.gettz('America/Buenos Aires')))[:-6]

def higherOrlower(direction): 	#CALL or PUT
	global candleId
	check, candleId=api.buy(BetAmount,CurrencyPair,direction,expirations_mode)

	if check:				
		print('¡Order Ok!')
	else:
		print('Sorry, order fail.')	
		

def asgale():					#Define Martingale
	global BetAmount
	estimatedEarning = BetAmount * coeficient 

	if status == 'L':			
		BetAmount = ((BetAmount + estimatedEarning) / coeficient)
		print(BetAmount)
	else:
		pass

def winOrLoose():				#Check if operation Win or Loose
	global status
	global tryOperation
	#global operationNumber	
	print("Waiting for result...")
	result = api.check_win_v3(candleId)		

	if result > 0:
		status = 'W'
		print('Cha-ching! +$'+str(result))
	elif result < 0:
		status = 'L'
		print('Operation lost, waiting 10 minutes to continue.')
		time.sleep(600)				
	else:
		status = 'T'
		print('Operation tie, waiting 10 minutes to continue.')

#######################################################################################################################################

loggin()				#Loggin on iq Option
setMode('PRACTICE') 	#Set practice mode
getBalance()			#Get account balance
print(CurrencyPair)		#Print pair to trade
setCoeficient() 		#Define coeficient
startStream() 			#Initialize stream to get realtime candles.

print('Bot is running and waiting for '+str(MAXSIZE)+' candles inline...')

#######################################################################################################################################

while executeLoop:			
	candle = api.get_realtime_candles(CurrencyPair,candleTime)  #get candles in realtime
	counter = 0													#Reset counter to 0 when starting the loop.
	time.sleep(0.025)											#Sleep 25ms to avoid getting bloqued.
	
	for candles in candle: 										#loop trough candles to get values (Only 1 loop cause only one candle is asked.)
		candleId = candle[candles]['id']
		candleOpen = candle[candles]['open']
		candleClose = candle[candles]['close']
		candleFrom = candle[candles]['from']

	if candleOpen < candleClose:								#Define if candle is Verde, Roja, Empate		
		d2 = {candleId: 'V'}
	elif candleOpen > candleClose:			
		d2 = {candleId: 'R'}		
	else:
		d2 = {candleId: 'E'}	

	if len(d) == (MAXSIZE-1): 									#Loop trought dictionary and set counter value to be compared with MAXSIZE in next step
		for key, value in d.items():
			if value == 'V':				
				counter = counter + 1						
			elif value == 'R':
				counter = counter - 1	
			elif value == 'E':
				counter = 0
				pass	

	if coeficient >= minCoeficient: 							#Operates only if profit is major or equal than minCoeficient

		if counter == (MAXSIZE-1):								#Do a PUT		
			higherOrlower('put')
			winOrLoose()

			if status =='W':
				executeLoop = True 
				print('¡Win! Resetting values and restarting...')
				d2 = {}										#Define d2 as empty to be empty updated on the last step
				resetValues() 								#resetea los valores para volver a iniciar					
				break

			else:
				executeLoop = True 
				print('Resetting values and restarting...')
				d2 = {}										#Define d2 as empty to be empty updated on the last step
				resetValues() 								#resetea los valores para volver a iniciar					
				break
				
		if counter == ((MAXSIZE-1) * -1):						#Do a CALL
			higherOrlower('call')
			winOrLoose()

			if status=='W':
				executeLoop = True 
				print('¡Win! Resetting values and restarting...')
				d2 = {}										#Define d2 as empty to be empty updated on the last step
				resetValues() 								#resetea los valores para volver a iniciar					
				break
				
			else:
				executeLoop = True 
				print('Resetting values and restarting...')
				d2 = {}										#Define d2 as empty to be empty updated on the last step
				resetValues() 								#resetea los valores para volver a iniciar					
				break

		else:
			pass

	if len(d) == MAXSIZE:										#Delefe first candle input on dictionary.
		del d[candleId - (MAXSIZE-1)] 
		print('Candle number '+str(candleId - (MAXSIZE-1))+' deleted.')
		#print('New candle started at: '+str(timestamp_converter(candleFrom))+' created.')
		setCoeficient()
	
	d.update(d2)
	




