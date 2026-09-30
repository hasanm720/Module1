// Module 5: Python calculates P control; Arduino measures and applies commands.
// Command: SET PWM 120 DIR HEAT\n (or COOL). Baud: 115200.
#include <Arduino.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

const int THERMISTOR_PIN = A0;
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
const unsigned long REPORT_INTERVAL_MS = 500;

int pwmValue = 0;
bool heating = true;
bool safetyShutdown = false;
bool sensorFault = false;
bool commandTimedOut = false;
bool haveCommand = false;
unsigned long lastCommandMs = 0;
unsigned long lastReportMs = 0;
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

float readTemperatureC() {
  unsigned long sum = 0;
  for (int i = 0; i < TEMPERATURE_SAMPLES; ++i) {
    sum += analogRead(THERMISTOR_PIN);
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

void report(float temperature) {
  Serial.print("Temperature (C): "); Serial.print(temperature, 2);
  Serial.print(", Time (s): "); Serial.print(millis() / 1000.0, 2);
  Serial.print(", PWM: "); Serial.print(pwmValue);
  Serial.print(", DIR: "); Serial.print(heating ? "HEAT" : "COOL");
  Serial.print(", Safety: ");
  if (sensorFault) Serial.print("SENSOR_FAULT");
  else if (safetyShutdown) Serial.print("SHUTDOWN");
  else if (commandTimedOut) Serial.print("TIMEOUT");
  else Serial.print("OK");
  Serial.print(", Limit (C): "); Serial.print(TEMPERATURE_LIMIT_C, 2);
  Serial.print(", PWM9: "); Serial.print(heating ? pwmValue : 0);
  Serial.print(", PWM10: "); Serial.println(heating ? 0 : pwmValue);
}

void setup() {
  Serial.begin(115200);
  pinMode(HEAT_PIN, OUTPUT);
  pinMode(COOL_PIN, OUTPUT);
  stopOutput();
}

void loop() {
  float temperature = readTemperatureC();
  checkSafety(temperature);  // Independent of Python; checked before commands.
  readCommands();
  if (haveCommand && millis() - lastCommandMs > COMMAND_TIMEOUT_MS) {
    commandTimedOut = true;
    stopOutput();
  }
  applyOutput();
  if (millis() - lastReportMs >= REPORT_INTERVAL_MS) {
    lastReportMs = millis();
    report(temperature);  // Continue measuring/reporting during every shutdown.
  }
}
