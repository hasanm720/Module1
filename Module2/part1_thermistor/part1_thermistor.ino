// ============================================================================
// Module 2 Thermistor Temperature Measurement - Serial Plotter Output
// ============================================================================

// Circuit and Hardware Constants
const int THERMISTOR_PIN = A0;      // Analog input pin connected to the divider node
const float V_REF = 5.0;            // Supply voltage / Reference voltage (Volts)
const float R_FIXED = 100000.0;     // Fixed series resistor value (100 kOhms)

// Thermistor Model Constants (Beta Model)
const float R0 = 100000.0;          // Thermistor nominal resistance at 25°C (100 kOhms)
const float T0_KELVIN = 298.15;     // Reference temperature in Kelvin (25°C = 298.15 K)
const float BETA = 3950.0;          // Thermistor Beta parameter (K) — adjust per datasheet

// Measurement and Timing Parameters
const int NUM_SAMPLES = 500;        // Number of samples to average (between 100 and 1000)
const unsigned long REPORT_INTERVAL_MS = 1000; // Delay between reports in milliseconds

// Global tracking for non-blocking loop timing
unsigned long lastReportTime = 0;

// Function Declarations
float averageAdcSamples();
float adcToVoltage(float adcAvg);
float voltageToResistance(float voltage);
float resistanceToCelsius(float resistance);
void printSerialPlotterValue(float tempC);

void setup() {
  Serial.begin(9600);
  while (!Serial) {
    ; // Wait for serial port to connect (needed for native USB boards)
  }
}

void loop() {
  unsigned long currentMillis = millis();

  // Check if it is time to take and report a new measurement
  if (currentMillis - lastReportTime >= REPORT_INTERVAL_MS) {
    lastReportTime = currentMillis;

    // 1. Average 100 to 1000 raw ADC readings
    float avgAdc = averageAdcSamples();

    // 2. Convert ADC counts to average voltage
    float avgVoltage = adcToVoltage(avgAdc);

    // 3. Calculate thermistor resistance from voltage divider equation
    float resistance = voltageToResistance(avgVoltage);

    // 4. Calculate temperature using Beta model equation
    float tempCelsius = resistanceToCelsius(resistance);

    // 5. Print single numeric temperature value for Arduino Serial Plotter
    printSerialPlotterValue(tempCelsius);
  }
}

/**
 * Reads the analog pin NUM_SAMPLES times and computes the arithmetic mean.
 */
float averageAdcSamples() {
  unsigned long adcSum = 0;
  for (int i = 0; i < NUM_SAMPLES; i++) {
    adcSum += analogRead(THERMISTOR_PIN);
  }
  return (float)adcSum / (float)NUM_SAMPLES;
}

/**
 * Converts average 10-bit ADC value (0-1023) to measured voltage.
 */
float adcToVoltage(float adcAvg) {
  return (adcAvg / 1023.0) * V_REF;
}

/**
 * Calculates thermistor resistance using the voltage divider formula:
 * Circuit layout: 5V -> Fixed Resistor (R_FIXED) -> A0 Node -> Thermistor (R_TH) -> GND
 * V_out = V_REF * R_TH / (R_FIXED + R_TH)  ==>  R_TH = R_FIXED * V_out / (V_REF - V_out)
 */
float voltageToResistance(float voltage) {
  if (voltage >= V_REF) return 1e6; // Prevent division by zero if output pegs high
  return R_FIXED * (voltage / (V_REF - voltage));
}

/**
 * Converts resistance to temperature in Celsius using the Beta Parameter equation:
 * 1/T = 1/T0 + (1/BETA) * ln(R / R0)
 */
float resistanceToCelsius(float resistance) {
  if (resistance <= 0.0) return -273.15; // Safeguard against non-physical inputs
  
  float invT = (1.0 / T0_KELVIN) + (1.0 / BETA) * log(resistance / R0);
  float tempKelvin = 1.0 / invT;
  return tempKelvin - 273.15; // Convert Kelvin to Celsius
}

/**
 * Outputs only the numerical temperature value on its own line for Serial Plotter compatibility.
 */
void printSerialPlotterValue(float tempC) {
  Serial.println(tempC, 1);
}