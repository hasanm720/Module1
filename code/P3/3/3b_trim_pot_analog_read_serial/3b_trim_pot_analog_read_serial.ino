/*
  AnalogReadSerial

  Reads an analog input on pin 0, prints the result to the Serial Monitor.
  Graphical representation is available using Serial Plotter (Tools > Serial Plotter menu).
  Attach the center pin of a potentiometer to pin A0, and the outside pins to +5V and ground.

  This example code is in the public domain.

  https://docs.arduino.cc/built-in-examples/basics/AnalogReadSerial/
*/

// the setup routine runs once when you press reset:
void setup() {
  // initialize serial communication at 9600 bits per second:
  Serial.begin(9600);
}

// the loop routine runs over and over again forever:
void loop() {
  float vref = 5.00;
  // read the input on analog pin 0:
  float sensorValue = analogRead(A0);
  float voltageValue = vref * (sensorValue/1023.00);
  // print out the value you read:
  Serial.println(voltageValue);
  delay(1);  // delay in between reads for stability
}

// Post-Class Notes
// Trim Pot maxV: 1018 minV: 55 (not in units of volts)
// nmid = (nmin + nmax)/2 = 536.5

// The order values change when you do not touch the ptentiometer because of thermal fluctuations
// They occupt discrete integer levels because the arduino converters uses 10 bits and can only then choose integers
// 
