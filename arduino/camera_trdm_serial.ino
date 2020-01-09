// specify the pins of the camera triggers outputs
int pinCam1 = 10; //BaslerCam
//int pinCam2 = 12; //XimeaCam

// specify the pin of treadmill speed input
int trdmSpeed_pin = A0;

// specify the pins of electrode inputs
//int emg1_pin = 6;
//int emg2_pin = 7;
//int emg3_pin = 8;
//int emg4_pin = 9;

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
int trdmRampUpEnd = 3000; // 3 seconds
int trdmMaxEnd = 8000; // 5 seconds
int trdmRampDownEnd = 11000; // 3 seconds

// initialise variables dependent on input from Python
int trdmMaxSpeed = 0; // for incoming serial data - max treadmill speed
int trdmIncrement = 0;
int trdmValue = 0;

int trdmSpeed_readout = 0;


void setup() {
  pinMode(pinCam1, OUTPUT);
  //pinMode(pinCam2, OUTPUT);
  
  pinMode(trdmSpeed_pin, INPUT); 

  //pinMode(emg1_pin, INPUT);
  //pinMode(emg2_pin, INPUT);
  //pinMode(emg3_pin, INPUT);
  //pinMode(emg4_pin, INPUT);
  
  pinMode(trdmRun_pin, OUTPUT);
 
  Serial.begin(115200);
}


void loop() {
  currentMillis = millis(); //get current time
  
  if (Serial.available() > 0) {
    // read the incoming byte, this will be the max voltage value of the chosen treadmill protocol
    trdmMaxSpeed = Serial.read();
    trdmIncrement = round(trdmMaxSpeed/trdmRampUpEnd);
    }
  
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
    trdmSpeed_readout = analogRead(trdmSpeed_pin); //get actual treadmill speed
  
    Serial.println(String(1.0)+";"+String(trdmSpeed_readout)); //send info to Python
    //Serial.println(String(1.0)+";"+String(trdmSpeed_readout)+";"+String(emg1_readout)+";"+String(emg2_readout)+";"+String(emg3_readout)+";"+String(emg4_readout));
    oldTrdmSpeedMillis = currentMillis;
  }  
    
  
  // control treadmill based on the maxSpeed input from Python
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