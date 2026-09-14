// ============================================================================
// Module 2 Thermistor Temperature Measurement - Serial Monitor Output
// ============================================================================

// -------------------------
// Circuit Constants
// -------------------------
const int THERMISTOR_PIN = A0;
const float V_REF = 5.0;
const float R_FIXED = 100000.0;     // 100 kOhm

// -------------------------
// Thermistor Constants
// -------------------------
const float R0 = 100000.0;          // Resistance at 25 C
const float T0_KELVIN = 298.15;     // 25 C in Kelvin
const float BETA = 3950.0;          // Beta parameter

// -------------------------
// Measurement Parameters
// -------------------------
const int NUM_SAMPLES = 100;        // Must be between 100 and 1000
const unsigned long REPORT_INTERVAL_MS = 1000;

// Keep track of time
unsigned long lastReportTime = 0;

// -------------------------
// Function Declarations
// -------------------------
float averageAdcSamples();
float adcToVoltage(float adcAvg);
float voltageToResistance(float voltage);
float resistanceToCelsius(float resistance);

void setup() {
  Serial.begin(9600);

  // Needed for some boards with native USB
  while (!Serial) {
    ;
  }
}

void loop() {

  unsigned long currentMillis = millis();

  // Take a new measurement every 1 second
  if (currentMillis - lastReportTime >= REPORT_INTERVAL_MS) {

    lastReportTime = currentMillis;

    // ------------------------------------------------
    // 1. Take NUM_SAMPLES raw ADC measurements
    // ------------------------------------------------
    float avgAdc = averageAdcSamples();

    // ------------------------------------------------
    // 2. Convert the AVERAGE ADC value to voltage
    // ------------------------------------------------
    float voltage = adcToVoltage(avgAdc);

    // ------------------------------------------------
    // 3. Calculate resistance from the average voltage
    // ------------------------------------------------
    float resistance = voltageToResistance(voltage);

    // ------------------------------------------------
    // 4. Calculate temperature from the resistance
    // ------------------------------------------------
    float temperature = resistanceToCelsius(resistance);

    // ------------------------------------------------
    // 5. Print human-readable measurement
    // ------------------------------------------------
    Serial.print("time = ");
    Serial.print(currentMillis / 1000.0, 2);
    Serial.print(" s    ");

    Serial.print("average ADC = ");
    Serial.print(avgAdc, 1);
    Serial.print("    ");

    Serial.print("voltage = ");
    Serial.print(voltage, 3);
    Serial.print(" V    ");

    Serial.print("resistance = ");
    Serial.print(resistance / 1000.0, 2);
    Serial.print(" kOhm    ");

    Serial.print("temperature = ");
    Serial.print(temperature, 1);
    Serial.print(" C    ");

    Serial.print("samples = ");
    Serial.println(NUM_SAMPLES);
  }
}


// ============================================================================
// Reads NUM_SAMPLES raw ADC measurements and calculates their average
// ============================================================================
float averageAdcSamples() {

  unsigned long adcSum = 0;

  for (int i = 0; i < NUM_SAMPLES; i++) {
    adcSum += analogRead(THERMISTOR_PIN);
  }

  return (float)adcSum / NUM_SAMPLES;
}


// ============================================================================
// Converts average ADC value to voltage
// ============================================================================
float adcToVoltage(float adcAvg) {

  return (adcAvg / 1023.0) * V_REF;
}


// ============================================================================
// Calculates thermistor resistance
//
// Circuit:
//
// 5V
//  |
// R_FIXED
//  |
//  +------ A0
//  |
// Thermistor
//  |
// GND
//
// Vout = V_REF * R_TH / (R_FIXED + R_TH)
//
// Therefore:
//
// R_TH = R_FIXED * Vout / (V_REF - Vout)
// ============================================================================
float voltageToResistance(float voltage) {

  if (voltage >= V_REF) {
    return 1e6;
  }

  if (voltage <= 0.0) {
    return 0.0;
  }

  return R_FIXED * voltage / (V_REF - voltage);
}


// ============================================================================
// Converts thermistor resistance to temperature using Beta model
//
// 1/T = 1/T0 + (1/BETA) * ln(R/R0)
// ============================================================================
float resistanceToCelsius(float resistance) {

  if (resistance <= 0.0) {
    return -273.15;
  }

  float invT =
    (1.0 / T0_KELVIN) +
    (1.0 / BETA) * log(resistance / R0);

  float temperatureKelvin = 1.0 / invT;

  return temperatureKelvin - 273.15;
}