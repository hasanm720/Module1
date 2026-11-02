// Module 7: Python retains PI control; Arduino measures six sensors and applies commands.
// Copy of the Arduino sketch used by Module 6. Original file is unchanged.
// TEC supply OFF while wiring/testing. Retain the existing H-bridge wiring and hardware safety.
// The TEC thermistor (A1) alone controls temperature shutdown. Rod temperatures never enter feedback.
// Python owns the setpoint; legacy PWM commands do not transmit it (reported as nan).
// Command: SET PWM 120 DIR HEAT\n (or COOL). Baud: 115200.
#include <Arduino.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

// Report order: TEC, rod1 (nearest TEC) ... rod5. Pins follow the bench wiring:
// TEC = A1, T1 = A5, T2 = A4, T3 = A3, T4 = A2, rod 5 = A0.
const byte SENSOR_COUNT = 6;
const byte TEC_SENSOR = 0;
const int THERMISTOR_PINS[SENSOR_COUNT] = {A1, A5, A4, A3, A2, A0};
const int HEAT_PIN = 9;
const int COOL_PIN = 10;
// Same divider and Beta-model constants as Module 4.
const float SERIES_RESISTOR = 100000.0;
const float R0 = 100000.0;
const float B_COEFF = 3950.0;
const float T0 = 298.15;
const int TEMPERATURE_SAMPLES = 1000;
const float TEMPERATURE_LIMIT_C = 60.0;
const unsigned long COMMAND_TIMEOUT_MS = 2000;

int pwmValue = 0;
bool heating = true;
bool safetyShutdown = false;
bool sensorFault = false;
bool commandTimedOut = false;
bool haveCommand = false;
unsigned long lastCommandMs = 0;
unsigned long lastByteMs = 0;
char commandBuffer[48];
byte commandLength = 0;
bool discardCommand = false;

void stopOutput() {
  pwmValue = 0;
  analogWrite(HEAT_PIN, 0);
  analogWrite(COOL_PIN, 0);
}

void applyOutput() {
  if (safetyShutdown || sensorFault || commandTimedOut) {
    stopOutput();
    return;
  }
  // Clear the opposite output BEFORE enabling the selected output.
  if (heating) {
    analogWrite(COOL_PIN, 0);
    analogWrite(HEAT_PIN, pwmValue);
  } else {
    analogWrite(HEAT_PIN, 0);
    analogWrite(COOL_PIN, pwmValue);
  }
}

// Average the same 1000 ADC readings per sensor, then convert once.
// Discard one conversion after changing channels to settle the multiplexed ADC.
float readTemperatureC(int pin) {
  analogRead(pin);
  unsigned long sum = 0;
  for (int i = 0; i < TEMPERATURE_SAMPLES; ++i) {
    sum += analogRead(pin);
  }
  // Average voltage/ADC first, then convert once to temperature.
  float averageADC = (float)sum / TEMPERATURE_SAMPLES;
  if (averageADC <= 0.0 || averageADC >= 1023.0) return NAN;
  float resistance = SERIES_RESISTOR * averageADC / (1023.0 - averageADC);
  float inverseT = log(resistance / R0) / B_COEFF + 1.0 / T0;
  return 1.0 / inverseT - 273.15;
}

void checkSafety(float temperature) {
  bool wasBlocked = safetyShutdown || sensorFault;
  sensorFault = !isfinite(temperature);
  safetyShutdown = !sensorFault && temperature > TEMPERATURE_LIMIT_C;
  if (sensorFault || safetyShutdown || wasBlocked) {
    // After recovery the old PWM remains zero. A new command is required.
    stopOutput();
  }
}

void processCommand() {
  // Parse strictly; reject trailing junk, missing PWM, or unknown direction.
  if (strncmp(commandBuffer, "SET PWM ", 8) != 0) {
    stopOutput();
    return;
  }
  char *start = commandBuffer + 8;
  char *end;
  long requestedPwm = strtol(start, &end, 10);
  if (end == start || requestedPwm < 0 || requestedPwm > 255 ||
      strncmp(end, " DIR ", 5) != 0) {
    stopOutput();
    return;
  }
  const char *direction = end + 5;
  bool requestedHeating;
  if (strcmp(direction, "HEAT") == 0) requestedHeating = true;
  else if (strcmp(direction, "COOL") == 0) requestedHeating = false;
  else {
    stopOutput();
    return;
  }
  if (safetyShutdown || sensorFault) {
    stopOutput();
    return;
  }
  heating = requestedHeating;
  pwmValue = (int)requestedPwm;
  lastCommandMs = millis();
  haveCommand = true;
  commandTimedOut = false;
  applyOutput();
}

void readCommands() {
  // Nonblocking, bounded work: a partial command never delays temperature checks.
  if (commandLength > 0 && millis() - lastByteMs > 1000) {
    stopOutput();
    commandLength = 0;
    discardCommand = true;
  }
  int budget = 64;
  while (Serial.available() > 0 && budget-- > 0) {
    char incoming = Serial.read();
    lastByteMs = millis();
    if (discardCommand) {
      if (incoming == '\n') discardCommand = false;
      continue;
    }
    if (incoming == '\r') continue;
    if (incoming == '\n') {
      commandBuffer[commandLength] = '\0';
      if (commandLength > 0) processCommand();
      commandLength = 0;
    } else if (incoming == '\0' || commandLength >= sizeof(commandBuffer) - 1) {
      stopOutput();
      commandLength = 0;
      discardCommand = true;
    } else {
      commandBuffer[commandLength++] = incoming;
    }
  }
}

// One complete CSV record per six-channel acquisition, including during shutdown.
// pwm is signed applied PWM; heat_cool is +1 for HEAT and -1 for COOL.
void report(const float temperatures[], unsigned long acquisitionMs) {
  Serial.print(F("DATA,"));
  Serial.print(acquisitionMs / 1000.0, 3);
  for (byte channel = 0; channel < SENSOR_COUNT; ++channel) {
    Serial.print(',');
    if (isfinite(temperatures[channel])) Serial.print(temperatures[channel], 2);
    else Serial.print(F("nan"));  // Preserve a missing/invalid channel visibly.
  }
  Serial.print(','); Serial.print(heating ? pwmValue : -pwmValue);
  Serial.print(','); Serial.print(heating ? 1 : -1);
  Serial.print(F(",nan,"));  // Setpoint stays in Python; never invent a temperature.
  if (sensorFault) Serial.println(F("SENSOR_FAULT"));
  else if (safetyShutdown) Serial.println(F("SHUTDOWN"));
  else if (commandTimedOut) Serial.println(F("TIMEOUT"));
  else Serial.println(F("OK"));
}

void setup() {
  Serial.begin(115200);
  pinMode(HEAT_PIN, OUTPUT);
  pinMode(COOL_PIN, OUTPUT);
  stopOutput();
  Serial.println(F("DATA,time_s,tec_C,rod1_C,rod2_C,rod3_C,rod4_C,rod5_C,pwm,heat_cool,setpoint_C,safety"));
}

void loop() {
  float temperatures[SENSOR_COUNT];
  // Check the TEC sensor before processing any command that could enable output.
  temperatures[TEC_SENSOR] = readTemperatureC(THERMISTOR_PINS[TEC_SENSOR]);
  checkSafety(temperatures[TEC_SENSOR]);
  readCommands();
  if (haveCommand && millis() - lastCommandMs > COMMAND_TIMEOUT_MS) {
    commandTimedOut = true;
    stopOutput();
  }
  applyOutput();

  // Rod channels are measurements only; they cannot override TEC (A1) shutdown.
  // Service commands and the original timeout between channel acquisitions.
  for (byte channel = 1; channel < SENSOR_COUNT; ++channel) {
    temperatures[channel] = readTemperatureC(THERMISTOR_PINS[channel]);
    readCommands();
    if (haveCommand && millis() - lastCommandMs > COMMAND_TIMEOUT_MS) {
      commandTimedOut = true;
      stopOutput();
    }
    applyOutput();
  }
  // Arduino timestamp is captured after all six measurements, as requested.
  // Report once per acquisition rather than dropping cycles on a report timer.
  unsigned long acquisitionMs = millis();
  report(temperatures, acquisitionMs);
}
