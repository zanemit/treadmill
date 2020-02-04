#include <Firmata.h>

// specify the pins of the camera triggers outputs
int pinCam1 = 10; //ximea
int pinCam2 = 11; //basler

// specify the pin of treadmill speed input
byte trdmSpeed_pin = 0;
byte emgGS_pin = 1;
byte emgTA_pin = 2;
byte emgST_pin = 3;
byte emgVL_pin = 4;

// define temporal variables
unsigned long oldCamMillis = 0;
unsigned long oldTrdmSpeedMillis = 0;
unsigned long currentMillis = 0;
  
int cameraOnEnd = 1; // on for 2 milliseconds
int cameraOffEnd = 4; // ~ TTL period, camera off for 3 milliseconds

void analogWriteCallback(byte pin, int value){
  pinMode(pin, OUTPUT);
  analogWrite(pin,value);
}

void setup() {
  pinMode(pinCam1, OUTPUT);
  pinMode(pinCam2, OUTPUT);

  Firmata.setFirmwareVersion(FIRMATA_FIRMWARE_MAJOR_VERSION, FIRMATA_FIRMWARE_MINOR_VERSION);
  Firmata.attach(ANALOG_MESSAGE, analogWriteCallback);
  Firmata.begin(57600);
}


void loop() {
  currentMillis = millis(); //get current time
  
  // control cameras
  if (currentMillis - oldCamMillis < cameraOnEnd){
    digitalWrite(pinCam1, HIGH); //turn BaslerCam on
    digitalWrite(pinCam2, HIGH); //turn XimeaCam on
  }
  
  else if (currentMillis - oldCamMillis < cameraOffEnd){
    digitalWrite(pinCam1, LOW); //turn BaslerCam off
    digitalWrite(pinCam2, LOW); //turn XimeaCam off
  }
  
  else{
    oldCamMillis = currentMillis;
  }
  
  
  // read and send information to Python every 5 milliseconds
  if (currentMillis - oldTrdmSpeedMillis >= 5){
    Firmata.sendAnalog(trdmSpeed_pin, analogRead(trdmSpeed_pin)); 
    Firmata.sendAnalog(emgGS_pin, analogRead(emgGS_pin));
    Firmata.sendAnalog(emgGS_pin, analogRead(emgTA_pin));
    Firmata.sendAnalog(emgGS_pin, analogRead(emgST_pin));
    Firmata.sendAnalog(emgGS_pin, analogRead(emgVL_pin));
  
    oldTrdmSpeedMillis = currentMillis;
  }  
}
