# !/usr/bin/env python
#include <wiringPi.h>

import Adafruit_DHT
import MySQLdb
import sys
import json
import os
import base64
import datetime

# Bibliotheken einbinden sonar
import RPi.GPIO as GPIO
import time
import datetime

#watertemp
#from w1thermsensor import W1ThermSensor


#display
#import wiringpi
import requests
import urllib.parse
#import adafruit_pcf8523
#import RPLCD


MAX_WATER_LEVEL = 4.3
MARGIN_WATER_LEVEL = 0.5

#disply variables
pcf8574_address = 0x3F
BASE = 64
RS = BASE+0
RW = BASE+1
EN = BASE+2
LED = BASE+3
D4 = BASE+4
D5 = BASE+5
D6 = BASE+6
D7 = BASE+7

#power

POWER_PIN1 = 18 #Light Top
POWER_PIN2 = 23 #Light Botoom
POWER_PIN3 = 24 #Fan Top
POWER_PIN4 = 25 #fan Bottom
POWER_PIN5 = 8 #AirPump
POWER_PIN6 = 7 #WaterPump
#POWER_PIN7 = 12 #NOT IN USE
POWER_PIN8 = 16 #Air Dehumditifier
#temp
pin = 21
pin2 = 20
waterPin = 4

#sonar
sonarTrigPin1 = 23
sonarEchoPin1 = 24
sonarTrigPin2 = 20
sonarEchoPin2 = 21

timeFormat = '%H:%M:%S';


def shouldLightSocketBeOn(socket):
    currentTime = getCurrentTime()
    isOn = False
    wakeupTime = datetime.datetime.strptime(socket['wakeupTime'], timeFormat)
    sleepTime = datetime.datetime.strptime(socket['sleepTime'], timeFormat)
    if wakeupTime <= currentTime <= sleepTime:
        isOn = True
    socket['lightOn'] = isOn
    return socket

def createSocketConfig(responseData):
    #map response to socket
    for socket in responseData:
        socket = shouldLightSocketBeOn(socket)
    return responseData


def getCurrentTime():
    currentTime = datetime.datetime.now().strftime(timeFormat)
    currentTime = datetime.datetime.strptime(currentTime, timeFormat)

    return currentTime



def takePhoto():
    os.system('fswebcam -r 1280x720 --no-banner /home/pi/webcam/temp/image.jpg')
    image = encodeImage()
    return image


def encodeImage():
    with open("/home/pi/webcam/temp/image.jpg", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
        return encoded_string


def getWaterTemp():
    #sensorWaterTemp = W1ThermSensor()
    #temperature = sensorWaterTemp.get_temperature()
    return 0#temperature


def setupPowerGPIO(LIGHT_RELAY_PIN):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LIGHT_RELAY_PIN, GPIO.OUT)



def setPowerOn(LIGHT_RELAY_PIN):
    GPIO.output(LIGHT_RELAY_PIN, GPIO.LOW)


def setPowerOFF(LIGHT_RELAY_PIN):
    GPIO.output(LIGHT_RELAY_PIN, GPIO.HIGH)


def removePowerGPIO(LIGHT_RELAY_PIN):
    GPIO.cleanup()


def isWaterLevelOk(waterLevel):
    if (waterLevel >= MAX_WATER_LEVEL + MARGIN_WATER_LEVEL):
        return False

    return True

# def showMessageOnScreen(message):
#     if (wiringPiSetup() == -1):
#         print("setup wiringPi failed !")
#         return 1



def getSonarDistance(sonarTrigPin, sonarEchoPin):
    # GPIO Modus (BOARD / BCM)
    GPIO.setmode(GPIO.BCM)

    # Richtung der GPIO-Pins festlegen (IN / OUT)
    GPIO.setup(sonarTrigPin, GPIO.OUT)
    GPIO.setup(sonarEchoPin, GPIO.IN)

    # setze Trigger auf HIGH
    GPIO.output(sonarTrigPin, True)

    # setze Trigger nach 0.01ms aus LOW
    time.sleep(0.00001)
    GPIO.output(sonarTrigPin, False)

    StartZeit = time.time()
    StopZeit = time.time()

    # speichere Startzeit
    while GPIO.input(sonarEchoPin) == 0:
        StartZeit = time.time()

    # speichere Ankunftszeit
    while GPIO.input(sonarEchoPin) == 1:
        StopZeit = time.time()

    # Zeit Differenz zwischen Start und Ankunft
    TimeElapsed = StopZeit - StartZeit
    # mit der Schallgeschwindigkeit (34300 cm/s) multiplizieren
    # und durch 2 teilen, da hin und zurueck
    distance = (TimeElapsed * 34300) / 2
    GPIO.cleanup()
    return distance


def loadPlantConfig():
    r = requests.get("https://easyplantserver.herokuapp.com/config/1")
    print(r.status_code, r.reason)
    print(r.text[:300] + '...')
    data = json.loads(r.text)
    print(data)
    return data

def getPlantData():
    sensor = Adafruit_DHT.DHT22
    loadPlantConfig()


    #db = MySQLdb.connect("e40762-mysql.services.easyname.eu", "u45962db6", "database", "u45962db6")
    #curs = db.cursor()

    waterLevel = 0#getSonarDistance(sonarTrigPin1, sonarEchoPin1)
    waterLevelStatus = 0#isWaterLevelOk(waterLevel)
    waterTemp = getWaterTemp()
    print('WaterTemp={0:0.1f}C '.format(waterTemp))
    #photo = open('/home/pi/webcam/temp/image.jpg', 'rb').read()
    #takePhoto()

    # distance2 = getSonarDistance(sonarTrigPin2, sonarEchoPin2)
    # Try to grab a sensor reading.  Use the read_retry method which will retry up
    # to 15 times to get a sensor reading (waiting 2 seconds between each retry).

    try:
        humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
        humidity2, temperature2 = Adafruit_DHT.read_retry(sensor, pin2)
        print("Temperature_Humidy_Sensor 1")
        print('Temp={0:0.1f}*  Humidity={1:0.1f}%'.format(temperature, humidity))
        print("Temperature_Humidy_Sensor 2")
        print('Temp={0:0.1f}*  Humidity={1:0.1f}%'.format(temperature2, humidity2))

        print('WaterLevel={0:0.1f}cm'.format(waterLevel))
        print('WaterLevelStatus={0}'.format(waterLevelStatus))
        # print('Distance2={0:0.1f}cm '.format(distance2))
        #showMessageOnScreen("test")
        #r = requests.get("https://easyplantserver.herokuapp.com/plants")
        headers = {
            'content-type': "application/x-www-form-urlencoded",
        }
        photoString = 'test'#rllib.parse.quote(photo)
        payload = "waterTemperature=0&plantId=1"
        #print(photoString)
        print('-----------------------')
        #print(photo)
        #print('decode')
        #print(photo.decode())
        data = {'waterTemperature':waterTemp, 'temperature1':temperature, 'temperature2':temperature2,'ph':0,'humidity':humidity,'waterLevel':0,'isFanOn':0,'isLight1On':0,'isLight2On':0,'isWaterPumpOn':0,'isDehumidifierOn':0,'image1': 0,'image2': photoString,'image3':0,'image4':0,'plantId': 1}
        #urllib.parse.urlencode(data)
        print(data['image1'])
        r = requests.request("POST", "https://easyplantserver.herokuapp.com/plants/update", data=data, headers=headers)
        print(r.text)
        print(r.status_code, r.reason)
        print(r.text[:300] + '...')
        print('photo')
        #print(photo)
        #curs.execute(
         #   "INSERT INTO temperatur_tb (datum, uhrzeit, temp, huminity, waterLevel, waterLevelStatus) VALUES (CURRENT_DATE(), NOW(), {0:0.1f}, {1:0.1f}, {2:0.01f}, {3});".format(
         #       temperature, humidity, waterLevel, waterLevelStatus))
        #db.commit()
        print("written in the database: temperatur_tb (--success--)")
        #photo.close()

    except (MySQLdb.Error, MySQLdb.Warning) as e:
        print('Failed to get reading. Try again!')
        print(e)
        print("Error when writing in the database (failed) rolling back")
        db.rollback()
        sys.exit(1)

POWER_PIN1 = 18 #Light Top
POWER_PIN2 = 23 #Light Botoom
POWER_PIN3 = 24 #Fan Top
POWER_PIN4 = 25 #fan Bottom
POWER_PIN5 = 8 #AirPump
POWER_PIN6 = 7 #WaterPump
#POWER_PIN7 = 12 #NOT IN USE
POWER_PIN8 = 16 #Air Dehumditifier

def turnPowerOff():
    setupPowerGPIO(POWER_PIN1)
    setupPowerGPIO(POWER_PIN2)
    setupPowerGPIO(POWER_PIN3)
    setupPowerGPIO(POWER_PIN4)
    setupPowerGPIO(POWER_PIN5)
    setupPowerGPIO(POWER_PIN6)
    setupPowerGPIO(POWER_PIN7)

    setPowerOFF(POWER_PIN1)
    print("Power 1 OFF")
    time.sleep(3)
    setPowerOFF(POWER_PIN2)
    print("Power 2 OFF")
    time.sleep(3)
    setPowerOFF(POWER_PIN3)
    print("Power 3 OFF")
    time.sleep(3)
    setPowerOFF(POWER_PIN4)
    print("Power 4 OFF")
    time.sleep(3)
    setPowerOFF(POWER_PIN5)
    print("Power 5 OFF")
    time.sleep(3)
    setPowerOFF(POWER_PIN6)
    print("Power 6 OFF")
    time.sleep(3)
    setPowerOFF(POWER_PIN8)
    print("Power 7 OFF")
    time.sleep(3)

    removePowerGPIO(POWER_PIN1)
    removePowerGPIO(POWER_PIN2)
    removePowerGPIO(POWER_PIN3)
    removePowerGPIO(POWER_PIN4)
    removePowerGPIO(POWER_PIN5)
    removePowerGPIO(POWER_PIN6)

print('starting')
print('setting relay with power')
setupPowerGPIO(POWER_PIN1)
setupPowerGPIO(POWER_PIN2)
setupPowerGPIO(POWER_PIN3)
setupPowerGPIO(POWER_PIN4)
setupPowerGPIO(POWER_PIN5)
setupPowerGPIO(POWER_PIN6)
setupPowerGPIO(POWER_PIN8)

POWER_PIN1 = 18 #Light Top
POWER_PIN2 = 23 #Light Botoom
POWER_PIN3 = 24 #Fan Top
POWER_PIN4 = 25 #fan Bottom
POWER_PIN5 = 8 #AirPump
POWER_PIN6 = 7 #WaterPump
#POWER_PIN7 = 12 #NOT IN USE
POWER_PIN8 = 16 #Air Dehumditifier

while(1):
    data = []
    #turnPowerOff()
    plant1 = {"id": 1, "pins": {"lightPins":[POWER_PIN1, POWER_PIN3]}, "wakeupTime": "7:00:00", "sleepTime": "22:00:00"}
    plant2 = {"id": 1, "pins": {"lightPins": [POWER_PIN2, POWER_PIN4, POWER_PIN6]}, "wakeupTime": "7:00:00",
              "sleepTime": "22:07:00"}
    #plant2 = {"id": 1, "pins": {"lightPins":[16]}, "wakeupTime": "2019-05-25 9:00:00", "sleepTime": "2019-05-25 20:00:00"}
    # plant2 = {"id": 2, "pins": {"lightPins":[18, 25]}, "wakeupTime": "2019-05-25 9:00:00", "sleepTime": "2019-05-25 23:00:00"}
    # plant3 = {"id": 3, "pins": {"lightPins":[16]}, "wakeupTime": "2019-05-25 9:00:00", "sleepTime": "2019-05-25 23:00:00"}
    # plant4 = {"id": 4, "pins": {"lightPins":[25]}, "wakeupTime": "2019-05-25 9:00:00", "sleepTime": "2019-05-25 23:00:00"}
    # plant5 = {"id": 5, "pins": {"lightPins":[24]}, "wakeupTime": "2019-05-25 9:00:00", "sleepTime": "2019-05-25 23:00:00"}
    # plant6 = {"id": 6, "pins": {"lightPins":[26]}, "wakeupTime": "2019-05-25 9:00:00", "sleepTime": "2019-05-25 23:00:00"}
    data.append(plant1)
    data.append(plant2)
    # data.append(plant3)
    # data.append(plant4)
    # data.append(plant5)
    # data.append(plant6)
    data = createSocketConfig(data)
    print('data', data)
    lightsOn = []
    lightsOff = []
    for plant in data:
        print(plant['id'])
        if (plant['lightOn']):
            for pin in plant['pins']['lightPins']:
                lightsOn.append(pin)
        else:
            for pin in plant['pins']['lightPins']:
                lightsOff.append(pin)

    #removing duplicates
    lightsOn = list(dict.fromkeys(lightsOn))
    lightsOff = list(dict.fromkeys(lightsOff))

    #checking for duplicates in off and on
    for lightPin in lightsOff:
        if lightPin in lightsOn:
            print('ERROR WRONG SETTING: TRYING TO SETUP PIN ON AND OFF. WILL TURN PIN ON ' + str(lightPin))
            lightsOff.remove(lightPin)

    for pin in lightsOn:
        setPowerOn(pin)
        print('set power on for pin: ' + str(pin))
        time.sleep(1)


    for pin in lightsOff:
        setPowerOFF(pin)
        #removePowerGPIO(pin)
        print('set power off for pin: ' + str(pin))


    time.sleep(20)
    # print('power 7 on')
    # setupPowerGPIO(POWER_PIN7)
    # setPowerOn(POWER_PIN7)
    # #getPlantData()
    # config = loadPlantConfig()
    # setupPowerGPIO(POWER_PIN1)
    # setupPowerGPIO(POWER_PIN2)
    # setupPowerGPIO(POWER_PIN3)
    # setupPowerGPIO(POWER_PIN4)
    # setupPowerGPIO(POWER_PIN5)
    # setupPowerGPIO(POWER_PIN6)



    time.sleep(5)

#turnOnLights()
#turnPowerOff()
