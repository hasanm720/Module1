// Pin Definitions
const int THERMISTOR_PIN = A0;  // Thermistor input
const int POT_PIN        = A1;  // Trim pot input
const int HBRIDGE_PIN9   = 9;   // H-bridge input 9
const int HBRIDGE_PIN10  = 10;  // H-bridge input 10
const int DIR_PIN        = 11;  // SPDT direction switch input

// Thermistor Circuit Variables
const float SERIES_RESISTOR = 100000.0; // Fixed resistor value (100k Ohms)
const float R0              = 100000.0; // Thermistor resistance at 25°C (100k Ohms)
const float B_COEFF         = 3950.0;   // Beta coefficient
const float T0              = 298.15;   // 25°C in Kelvin

void setup() {
  Serial.begin(9600);

  // Set pins as outputs/inputs
  pinMode(HBRIDGE_PIN9, OUTPUT);
  pinMode(HBRIDGE_PIN10, OUTPUT);
  pinMode(DIR_PIN, INPUT);

  // Ensure initial PWM output starts at zero
  analogWrite(HBRIDGE_PIN9, 0);
  analogWrite(HBRIDGE_PIN10, 0); 
}

void loop() {
  // Read raw thermistor ADC
  int rawADC = analogRead(THERMISTOR_PIN);

  // Clamp ADC to avoid 0 or 1023 (division by zero / infinite resistance)
  if (rawADC >= 1023) rawADC = 1022;
  if (rawADC <= 0) rawADC = 1;

  // Calculate Thermistor Resistance (Thermistor to GND, Resistor to 5V)
  float rTherm = SERIES_RESISTOR * ((float)rawADC / (1023.0 - (float)rawADC));

  // Steinhart-Hart / Beta Equation for Temperature in Kelvin
  float steinhart = log(rTherm / R0) / B_COEFF; 
  steinhart += 1.0 / T0;                         
  float tempK = 1.0 / steinhart;                 

  // Convert Kelvin to Celsius
  float tempC = tempK - 273.15;

  // Read trim pot (0-1023) and map directly to PWM (0-255)
  int pwmVal = map(analogRead(POT_PIN), 0, 1023, 0, 255);

  // Read direction switch state on Pin 11
  int dirState = digitalRead(DIR_PIN);

  // Hardware direction routing logic
  int activePin;
  if (dirState == HIGH) { // 5V setting
    analogWrite(HBRIDGE_PIN9, pwmVal);
    digitalWrite(HBRIDGE_PIN10, LOW);
    activePin = HBRIDGE_PIN9;
  } else {                // 0V setting
    digitalWrite(HBRIDGE_PIN9, LOW);
    analogWrite(HBRIDGE_PIN10, pwmVal);
    activePin = HBRIDGE_PIN10;
  }

  // Print single line output required for Part 3
  Serial.print("Temperature (C): ");
  Serial.print(tempC, 2);
  Serial.print(", Time (s): ");
  Serial.print(millis() / 1000.0, 2);
  Serial.print(", PWM: ");
  Serial.print(pwmVal);
  Serial.print(", Pin 11 State: ");
  Serial.print(dirState == HIGH ? "5V" : "0V");
  Serial.print(", Active PWM pin: ");
  Serial.println(activePin);

  delay(500);
}