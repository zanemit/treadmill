// specify the pins of the camera triggers outputs
int pinCam1 = 10; //BaslerCam
//int pinCam2 = 12; //XimeaCam

// specify the pin of treadmill speed input
int trdmSpeed_pin = 6;

// specify the pins of electrode inputs
//int emg1_pin = 6;
//int emg2_pin = 7;
//int emg3_pin = 8;
//int emg4_pin = 9;

// define temporal variables
unsigned long oldCamMillis = 0;
unsigned long currentMillis = 0;
  
int cameraOnEnd = 2; // on for 2 milliseconds
int cameraOffEnd = 5; // ~ TTL period, camera off for 3 milliseconds


void setup() {
  pinMode(pinCam1, OUTPUT);
  //pinMode(pinCam2, OUTPUT);
  
  pinMode(trdmSpeed_pin, INPUT); 

  //pinMode(emg1_pin, INPUT);
  //pinMode(emg2_pin, INPUT);
  //pinMode(emg3_pin, INPUT);
  //pinMode(emg4_pin, INPUT);
 
  Serial.begin(115200);
}


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
  if (currentMillis % cameraOffEnd == 0){
    trdmSpeed_readout = analogRead(trdmSpeed_pin); //get actual treadmill speed

    //emg1_readout = digitalRead(emg1_pin);
    //emg2_readout = digitalRead(emg2_pin);
    //emg3_readout = digitalRead(emg3_pin);
    //emg4_readout = digitalRead(emg4_pin);
  
    Serial.println(String(1.0)+";"+String(trdmSpeed_readout)); //send info to Python
    //Serial.println(String(1.0)+";"+String(trdmSpeed_readout)+";"+String(emg1_readout)+";"+String(emg2_readout)+";"+String(emg3_readout)+";"+String(emg4_readout));
    }  
}
