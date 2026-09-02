//LED DUTYCYCLE

const int potPin = A0;
const int pwmPin = 9;

const int average_timescale = 1000;
const float vref = 5.0;


void setup() {

  Serial.begin(9600);

  pinMode(pwmPin, OUTPUT);
}


void loop() {

  // AVERAGED ADC NUMBER
  

  long sensor_value_sum = 0;

  for (int j = 0; j < average_timescale; j++) {

    sensor_value_sum += analogRead(potPin);
  }

  float average_sensor_value =
    sensor_value_sum / (float)average_timescale;


  
  // CONVERT ADC NUMBER TO VOLTAGE
  

  float voltageValue =
    vref * (average_sensor_value / 1023.0);


  // MAP ADC NUMBER TO PWM VALUE

  int pwmValue =
    (average_sensor_value/4);


  // OUTPUT PWM
  
  analogWrite(9, pwmValue);


  // PRINT VALUES

  Serial.print("Average ADC = ");
  Serial.print(average_sensor_value, 2);

  Serial.print("   Voltage = ");
  Serial.print(voltageValue, 4);

  Serial.print(" V   PWM = ");
  Serial.println(pwmValue);

  delay(50);
}