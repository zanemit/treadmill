#include <Firmata.h>
/*==============================================================================
 * GLOBAL VARIABLES
 *============================================================================*/

// specify the pins of the camera triggers outputs
int pinCam1 = 10; //BaslerCam
//int pinCam2 = 12; //XimeaCam

// specify the pin of treadmill speed input
byte trdmSpeed_pin = 0; // A0 pin

// specify the pin of motor output
int trdmRun_pin = ;

// define temporal variables
unsigned long oldCamMillis = 0;
unsigned long oldTrdmMillis = 0;
unsigned long oldRampMillis = 0;
unsigned long oldTrdmSpeedMillis = 0;
unsigned long currentMillis = 0;
  
int cameraOnEnd = 2; // on for 2 milliseconds
int cameraOffEnd = 5; // ~ TTL period, camera off for 3 milliseconds
int trdmRampUpEnd = 5000; // 5 seconds
int trdmMaxEnd = 10000; // 5 seconds
int trdmRampDownEnd = 15000; // 5 seconds

int trdmMaxSpeed = 200;

/*==============================================================================
 * FUNCTIONS
 *============================================================================*/

void analogWriteCallback(byte pin, int value){
  pinMode(pin, OUTPUT);
  analogWrite(pin,value);
}

/*==============================================================================
 * SETUP
 *============================================================================*/
void setup() {
  pinMode(pinCam1, OUTPUT);
  //pinMode(pinCam2, OUTPUT);
  
  Firmata.setFirmwareVersion(FIRMATA_FIRMWARE_MAJOR_VERSION, FIRMATA_FIRMWARE_MINOR_VERSION);
  Firmata.attach(ANALOG_MESSAGE, analogWriteCallback);
  Firmata.begin(57600);
}

/*==============================================================================
 * LOOP
 *============================================================================*/
void loop() {
  currentMillis = millis(); //get current time
  
  // control cameras
  if (currentMillis - oldCamMillis < cameraOnEnd){
    digitalWrite(pinCam1, HIGH); //turn BaslerCam on
    //digitalWrite(pinCam2, HIGH); //turn XimeaCam on
  }
  
  else if (currentMillis - oldCamMillis < cameraOffEnd){
    digitalWrite(pinCam1, LOW); //turn BaslerCam off
    //digitalWrite(pinCam2, LOW); //turn XimeaCam off
  }
  
  else{
    oldCamMillis = currentMillis;
  }
  
  
  // read and send information to Python every 5 milliseconds
  if (currentMillis - oldTrdmSpeedMillis >= 5){
    Firmata.sendAnalog(trdmSpeed_pin, analogRead(trdmSpeed_pin));  
    oldTrdmSpeedMillis = currentMillis;
  }  
  
  
  // control treadmill based on trdmMaxSpeed 
  if (currentMillis - oldTrdmMillis < trdmRampUpEnd){ //ramp up
    if (currentMillis - oldRampMillis < 1){
      analogWrite(trdmRun_pin, trdmValue);
    }
    else { //update once every millisecond
      trdmValue = trdmValue + trdmIncrement;
      analogWrite(trdmRun_pin, trdmValue);
      oldRampMillis = currentMillis;
    }
  }
  
  else if (currentMillis - oldTrdmMillis < trdmMaxEnd){ //max speed
    trdmValue = trdmMaxSpeed;
    analogWrite(trdmRun_pin, trdmValue);
    oldRampMillis = currentMillis;
  }
  
  else if (currentMillis - oldTrdmMillis < trdmRampDownEnd){ //ramp down
    if (currentMillis - oldRampMillis < 1){
      analogWrite(trdmRun_pin, trdmValue);
    }
    else { //update once every millisecond
      trdmValue = trdmValue - trdmIncrement;
      analogWrite(trdmRun_pin, trdmValue);
      oldRampMillis = currentMillis;
    }
  }
}
