// Pin Definitions
const int TRIM_POT_PIN = A1;    // Trim pot analog input pin
const int MODE_PIN     = 11;    // Heat/Cool mode toggle input pin
const int HEAT_PWM_PIN = 9;     // RPWM pin for H-bridge (Heat / Clockwise)
const int COOL_PWM_PIN = 10;    // LPWM pin for H-bridge (Cool / Counterclockwise)

// Measurement Constants
const int NUM_SAMPLES  = 100;   // Number of samples to average

void setup() {
  pinMode(MODE_PIN, INPUT);
  pinMode(HEAT_PWM_PIN, OUTPUT);
  pinMode(COOL_PWM_PIN, OUTPUT);
  
  Serial.begin(9600);
}

void loop() {
  // 1. Read and average the trim pot input
  long adcSum = 0;
  for (int i = 0; i < NUM_SAMPLES; i++) {
    adcSum += analogRead(TRIM_POT_PIN);
  }
  float avgAdc = (float)adcSum / NUM_SAMPLES;

  // 2. Map the 10-bit ADC average (0 - 1023) to an 8-bit PWM value (0 - 255)
  int pwmValue = map((int)avgAdc, 0, 1023, 0, 255);

  // 3. Read the mode pin (5V = HIGH for Heat, 0V = LOW for Cool)
  int modeState = digitalRead(MODE_PIN);

  // 4. Set the H-bridge command signals according to Method 2 logic
  if (modeState == HIGH) {
    // Heat / Clockwise mode
    analogWrite(HEAT_PWM_PIN, pwmValue); // PWM output to Pin 9
    analogWrite(COOL_PWM_PIN, 0);        // 0V (OFF) on Pin 10
  } else {
    // Cool / Counterclockwise mode
    analogWrite(HEAT_PWM_PIN, 0);        // 0V (OFF) on Pin 9
    analogWrite(COOL_PWM_PIN, pwmValue); // PWM output to Pin 10
  }

  // Debugging output for Serial Monitor
  Serial.print("Mode: ");
  Serial.print(modeState == HIGH ? "HEAT" : "COOL");
  Serial.print(" | Avg ADC: ");
  Serial.print(avgAdc, 1);
  Serial.print(" | PWM Command: ");
  Serial.println(pwmValue);

  delay(50); // Small delay for readability and stability
}