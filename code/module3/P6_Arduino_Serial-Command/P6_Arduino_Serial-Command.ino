// P6: Manual TEC control by serial command.
// Commands accepted from Python:
//   SET PWM 120 DIR HEAT
//   SET PWM 45 DIR COOL
// This is manual control only.  Temperature is measured and reported, but it
// never changes the PWM or direction automatically.

#include <string.h>
#include <stdio.h>

// Hardware kept from the manual trim-pot circuit.
const int THERMISTOR_PIN = A0;
const int HBRIDGE_PIN9 = 9;
const int HBRIDGE_PIN10 = 10;

// Take several A0 readings before calculating temperature to reduce ADC noise.
const byte THERMISTOR_SAMPLES = 10;
const float SERIES_RESISTOR = 100000.0;
const float R0 = 100000.0;
const float B_COEFF = 3950.0;
const float T0 = 298.15;

// The TEC begins off.  The direction is retained so the next valid command can
// select it, but PWM remains zero until a valid command is received.
int pwmValue = 0;
bool isHeating = true;

char commandBuffer[48];
byte commandLength = 0;
unsigned long lastReportMs = 0;


void applyHBridge() {
  // Experimentally verified direction mapping:
  // HEAT: PWM on pin 9 and pin 10 LOW.
  // COOL: pin 9 LOW and PWM on pin 10.
  // One input is always LOW, preventing both H-bridge inputs being driven at once.
  if (isHeating) {
    analogWrite(HBRIDGE_PIN9, pwmValue);
    digitalWrite(HBRIDGE_PIN10, LOW);
  } else {
    digitalWrite(HBRIDGE_PIN9, LOW);
    analogWrite(HBRIDGE_PIN10, pwmValue);
  }
}


void stopForBadCommand() {
  // Safety behavior: bad, incomplete, or unknown commands always turn the TEC off.
  // Direction is left unchanged because zero PWM means neither H-bridge direction
  // receives drive.
  pwmValue = 0;
  applyHBridge();
}


void parseCommand() {
  long requestedPwm;
  char requestedDirection[6];
  char unexpectedExtra;

  // sscanf returns 2 only for exactly "SET PWM <number> DIR HEAT|COOL".
  // The third conversion detects extra words, which makes that command malformed.
  int fieldsRead = sscanf(commandBuffer, "SET PWM %ld DIR %5s %c",
                          &requestedPwm, requestedDirection, &unexpectedExtra);
  if (fieldsRead != 2) {
    stopForBadCommand();
    Serial.println("ERROR: Malformed command; PWM set to 0.");
    return;
  }

  if (strcmp(requestedDirection, "HEAT") == 0) {
    isHeating = true;
  } else if (strcmp(requestedDirection, "COOL") == 0) {
    isHeating = false;
  } else {
    stopForBadCommand();
    Serial.println("ERROR: Unknown direction; PWM set to 0.");
    return;
  }

  // A valid numeric command is safely limited to Arduino's 8-bit PWM range.
  if (requestedPwm < 0) {
    pwmValue = 0;
  } else if (requestedPwm > 255) {
    pwmValue = 255;
  } else {
    pwmValue = (int)requestedPwm;
  }
  applyHBridge();
}


void readSerialCommands() {
  // Collect a command one character at a time.  This keeps the loop responsive
  // instead of pausing temperature reporting while waiting for serial text.
  while (Serial.available() > 0) {
    char incoming = Serial.read();
    if (incoming == '\r') {
      continue;  // Accept both LF and CRLF line endings.
    }

    if (incoming == '\n') {
      commandBuffer[commandLength] = '\0';
      if (commandLength > 0) {
        parseCommand();
      }
      commandLength = 0;
    } else if (commandLength < sizeof(commandBuffer) - 1) {
      commandBuffer[commandLength++] = incoming;
    } else {
      // An overlong command cannot be trusted, so discard it and stop the TEC.
      commandLength = 0;
      stopForBadCommand();
      Serial.println("ERROR: Command too long; PWM set to 0.");
    }
  }
}


float readAveragedTemperatureC() {
  long adcTotal = 0;
  for (byte sample = 0; sample < THERMISTOR_SAMPLES; sample++) {
    adcTotal += analogRead(THERMISTOR_PIN);
  }

  float averageAdc = (float)adcTotal / THERMISTOR_SAMPLES;
  averageAdc = constrain(averageAdc, 1.0, 1022.0);  // Avoid divide-by-zero values.
  float thermistorResistance = SERIES_RESISTOR * averageAdc / (1023.0 - averageAdc);
  float inverseTemperature = log(thermistorResistance / R0) / B_COEFF + (1.0 / T0);
  return (1.0 / inverseTemperature) - 273.15;
}


void printTelemetry() {
  // Heat/Cool reports the selected, experimentally verified H-bridge direction:
  // 1 means pin 9 (HEAT); 0 means pin 10 (COOL).  It does not implement feedback.
  Serial.print("Temperature (C): ");
  Serial.print(readAveragedTemperatureC(), 2);
  Serial.print(", Time (s): ");
  Serial.print(millis() / 1000.0, 2);
  Serial.print(", PWM: ");
  Serial.print(pwmValue);
  Serial.print(", Heat/Cool: ");
  Serial.println(isHeating ? 1 : 0);
}


void setup() {
  Serial.begin(9600);
  pinMode(HBRIDGE_PIN9, OUTPUT);
  pinMode(HBRIDGE_PIN10, OUTPUT);
  applyHBridge();  // PWM is zero at startup.
}


void loop() {
  readSerialCommands();

  // Report twice each second without using delay(), so GUI commands stay prompt.
  if (millis() - lastReportMs >= 500) {
    lastReportMs = millis();
    printTelemetry();
  }
}
