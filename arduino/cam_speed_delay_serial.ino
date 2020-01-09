// specify the pins of the camera triggers outputs
int pinCam1 = 10; //basler
//int pinCam2 = 12; //ximea

// specify the pin of treadmill speed input
int trdmSpeed_pin = A0;

int trdmSpeed_readout = 0;

void setup() {
  pinMode(pinCam1, OUTPUT);
  //pinMode(pinCam2, OUTPUT);
  
  pinMode(trdmSpeed_pin, INPUT); 

 Serial.begin(115200);
}

void loop() {
  digitalWrite(pinCam1, HIGH);
  //digitalWrite(pinCam2, HIGH);
  delay(2); // <- change this to modify framerate
  
  trdmSpeed_readout = analogRead(trdmSpeed_pin);


  Serial.println(String(1.0)+";"+String(trdmSpeed_readout));

  digitalWrite(pinCam1, LOW);
  //digitalWrite(pinCam2, LOW);
  delay(3); // <- change this to modify framerate
  
  Serial.println(String(0.0)+";"+String(trdmSpeed_readout));
}
