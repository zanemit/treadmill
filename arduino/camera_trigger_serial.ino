// specify the pins of the camera triggers outputs
int pinCam1 = 12;
int pinCam2 = 10;

// specify the pin of treadmill speed input
int trdmSpeed = 11;

// specify the pins of electrode inputs
//int emg1_pin = 6;
//int emg2_pin = 7;
//int emg3_pin = 8;
//int emg4_pin = 9;

void setup() {
  pinMode(pinCam1, OUTPUT);
  pinMode(pinCam2, OUTPUT);
  
  pinMode(trdmSpeed, INPUT); 

  //pinMode(emg1_pin, INPUT);
  //pinMode(emg2_pin, INPUT);
  //pinMode(emg3_pin, INPUT);
  //pinMode(emg4_pin, INPUT);

 Serial.begin(115200);
}

void loop() {
  digitalWrite(pinCam1, HIGH);
  digitalWrite(pinCam2, HIGH);
  delay(2); // <- change this to modify framerate
  
  trdmSpeed_readout = digitalRead(trdmSpeed);

  //emg1_readout = digitalRead(emg1_pin);
  //emg2_readout = digitalRead(emg2_pin);
  //emg3_readout = digitalRead(emg3_pin);
  //emg4_readout = digitalRead(emg4_pin);
  
  Serial.println(String(1.0)+";"+String(trdmSpeed_readout));
  //Serial.println(String(1.0)+";"+String(trdmSpeed_readout)+";"+String(emg1_readout)+";"+String(emg2_readout)+";"+String(emg3_readout)+";"+String(emg4_readout));

  digitalWrite(pinCam1, LOW);
  digitalWrite(pinCam2, LOW);
  delay(3); // <- change this to modify framerate
  
  Serial.println(String(0.0)+";"+String(trdmSpeed_readout));
 // Serial.println(String(0.0)+";"+String(trdmSpeed_readout)+";"+String(emg1_readout)+";"+String(emg2_readout)+";"+String(emg3_readout)+";"+String(emg4_readout));
}
