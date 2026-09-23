// Manual TEC control from P5_Manual_heat_cool_display.py.
// The Python GUI sends commands such as: SET PWM 120 DIR HEAT
// This sketch deliberately has no temperature feedback control.

// Pin definitions
const int THERMISTOR_PIN = A0;
const int HBRIDGE_PIN9 = 9;
const int HBRIDGE_PIN10 = 10;

// Thermistor circuit constants
const float SERIES_RESISTOR = 100000.0;
const float R0 = 100000.0;
const float B_COEFF = 3950.0;
const float T0 = 298.15;

// Values last received from the GUI.  Start with the TEC off for safety.
int pwmValue = 0;
bool heating = true;

// Buffer used to collect one newline-terminated command from the computer.
char commandBuffer[48];
byte commandLength = 0;
unsigned long lastReportMs = 0;


void applyTecOutput() {
  // Never PWM both H-bridge inputs at the same time.
  // If heat/cool is reversed for your wiring, swap the two sections below.
  if (heating) {
    analogWrite(HBRIDGE_PIN9, pwmValue);
    digitalWrite(HBRIDGE_PIN10, LOW);
  } else {
    digitalWrite(HBRIDGE_PIN9, LOW);
    analogWrite(HBRIDGE_PIN10, pwmValue);
  }
}


void processCommand() {
  int requestedPwm;
  char requestedDirection[6];

  // Accept exactly the command format sent by the Python GUI.
  if (sscanf(commandBuffer, "SET PWM %d DIR %5s", &requestedPwm, requestedDirection) != 2) {
    Serial.print("ERROR: Invalid command: ");
    Serial.println(commandBuffer);
    return;
  }

  // Keep PWM in the legal analogWrite range even if a bad command arrives.
  pwmValue = constrain(requestedPwm, 0, 255);

  if (strcmp(requestedDirection, "HEAT") == 0) {
    heating = true;
  } else if (strcmp(requestedDirection, "COOL") == 0) {
    heating = false;
  } else {
    Serial.println("ERROR: Direction must be HEAT or COOL.");
    return;
  }

  applyTecOutput();
  Serial.print("COMMAND ACCEPTED: SET PWM ");
  Serial.print(pwmValue);
  Serial.print(" DIR ");
  Serial.println(heating ? "HEAT" : "COOL");
}


void readSerialCommands() {
  // Read available characters without delay(), so a slider movement is applied promptly.
  while (Serial.available() > 0) {
    char incoming = Serial.read();

    if (incoming == '\r') {
      continue;  // Ignore the carriage return in CRLF line endings.
    }
    if (incoming == '\n') {
      commandBuffer[commandLength] = '\0';
      if (commandLength > 0) {
        processCommand();
      }
      commandLength = 0;
    } else if (commandLength < sizeof(commandBuffer) - 1) {
      commandBuffer[commandLength++] = incoming;
    } else {
      // Drop an overlong command rather than writing past the end of the buffer.
      commandLength = 0;
      Serial.println("ERROR: Command too long.");
    }
  }
}


float readTemperatureC() {
  int rawADC = analogRead(THERMISTOR_PIN);
  rawADC = constrain(rawADC, 1, 1022);  // Avoid division by zero.

  float thermistorResistance = SERIES_RESISTOR *
      ((float)rawADC / (1023.0 - (float)rawADC));
  float steinhart = log(thermistorResistance / R0) / B_COEFF;
  steinhart += 1.0 / T0;
  return (1.0 / steinhart) - 273.15;
}


void reportTelemetry() {
  // The Python program parses this line for its readouts, plot, and CSV file.
  Serial.print("Temperature (C): ");
  Serial.print(readTemperatureC(), 2);
  Serial.print(", Time (s): ");
  Serial.print(millis() / 1000.0, 2);
  Serial.print(", PWM: ");
  Serial.print(pwmValue);
  Serial.print(", DIR: ");
  Serial.println(heating ? "HEAT" : "COOL");
}


void setup() {
  Serial.begin(9600);
  pinMode(HBRIDGE_PIN9, OUTPUT);
  pinMode(HBRIDGE_PIN10, OUTPUT);
  applyTecOutput();
}


void loop() {
  readSerialCommands();

  // Send a measurement twice per second without blocking command reception.
  if (millis() - lastReportMs >= 500) {
    lastReportMs = millis();
    reportTelemetry();
  }
}
