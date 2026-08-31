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
  int Nsequential_steps = 100;
  int average_timescale = 1000;
  float vref = 5;
  // first 100 sequential voltage values (unaveraged)
  for (int i = 0; i < Nsequential_steps; i++){
    float sensorValue = analogRead(A0);
    float voltageValue = vref * (sensorValue/1023.00);
    // print out the value you read:
    Serial.print("Ave1_Point_");
    Serial.print(i);
    Serial.print(" Voltage_V:");
    Serial.println(voltageValue, 4);
    delay(1);  // delay in between reads for stability
  }
  // second 100 sequential voltage values (each averaged from 1000 readings)
  for (int i = 0; i < Nsequential_steps; i++){
    float sensor_value_sum = 0;
    for (int j = 0; j < average_timescale; j++){
      float sensorValue = analogRead(A0);
      sensor_value_sum = sensor_value_sum + sensorValue;
    }
    float average_sensor_value = sensor_value_sum/average_timescale;
    // converts 10 bit to voltage
    float voltageValue = vref * (average_sensor_value/1023.00);
    // print out the value you read:
    Serial.print("Ave1000_Point_");
    Serial.print(i);
    Serial.print(" Voltage_V:");
    Serial.println(voltageValue, 4);
    delay(1);
    delay(1);  // delay in between reads for stability
  }
}

// Post-Class Notes
// Trim Pot maxV: 1018 minV: 55 (not in units of volts)
// nmid = (nmin + nmax)/2 = 536.5

// The order values change when you do not touch the ptentiometer because of thermal fluctuations
// They occupt discrete integer levels because the arduino converters uses 10 bits and can only then choose integers
// 
