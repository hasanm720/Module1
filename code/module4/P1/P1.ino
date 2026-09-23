// Manual TEC control from P5_Manual_heat_cool_display.py.
// The Python GUI sends commands such as: SET PWM 120 DIR HEAT
//
// Module 4 additions:
//   1. Average 500 thermistor ADC measurements.
//   2. Software temperature safety limit at 60 C.
//   3. If T > 60 C, both H-bridge PWM outputs are forced to 0.
//   4. Temperature telemetry continues during a safety shutdown.
//
// This sketch is still OPEN LOOP:
// There is NO automatic temperature feedback control.
// The user/Python GUI still determines the requested PWM and direction.

// --------------------------------------------------
// Pin definitions
// --------------------------------------------------
const int THERMISTOR_PIN = A0;
const int HBRIDGE_PIN9 = 9;
const int HBRIDGE_PIN10 = 10;


// --------------------------------------------------
// Thermistor circuit constants
// --------------------------------------------------
const float SERIES_RESISTOR = 100000.0;
const float R0 = 100000.0;
const float B_COEFF = 3950.0;
const float T0 = 298.15;


// --------------------------------------------------
// Module 4 temperature-safety settings
// --------------------------------------------------
const float TEMPERATURE_LIMIT_C = 60.0;

// Number of ADC readings averaged for each temperature measurement.
const int TEMPERATURE_SAMPLES = 500;


// --------------------------------------------------
// Values last received from the GUI.
// Start with the TEC off for safety.
// --------------------------------------------------
int pwmValue = 0;
bool heating = true;

// True when the software temperature limit has been exceeded.
bool safetyShutdown = false;


// --------------------------------------------------
// Buffer used to collect one newline-terminated command
// from the computer.
// --------------------------------------------------
char commandBuffer[48];
byte commandLength = 0;

unsigned long lastReportMs = 0;


// --------------------------------------------------
// Apply TEC output
// --------------------------------------------------
void applyTecOutput() {

  // Safety always has priority.
  // If the temperature limit has been exceeded,
  // BOTH H-bridge inputs must be off.
  if (safetyShutdown) {
    analogWrite(HBRIDGE_PIN9, 0);
    analogWrite(HBRIDGE_PIN10, 0);
    return;
  }

  // Never PWM both H-bridge inputs at the same time.
  // If heat/cool is reversed for your wiring,
  // swap the two sections below.

  if (heating) {

    analogWrite(HBRIDGE_PIN9, pwmValue);
    digitalWrite(HBRIDGE_PIN10, LOW);

  } else {

    digitalWrite(HBRIDGE_PIN9, LOW);
    analogWrite(HBRIDGE_PIN10, pwmValue);
  }
}


// --------------------------------------------------
// Read thermistor temperature
//
// Takes 500 ADC measurements and averages them before
// converting the result into resistance and temperature.
// --------------------------------------------------
float readTemperatureC() {

  unsigned long adcSum = 0;

  // Take 500 measurements.
  for (int i = 0; i < TEMPERATURE_SAMPLES; i++) {
    adcSum += analogRead(THERMISTOR_PIN);
  }

  // Calculate the average ADC value.
  float rawADC = (float)adcSum / TEMPERATURE_SAMPLES;

  // Avoid division by zero and extreme ADC values.
  rawADC = constrain(rawADC, 1.0, 1022.0);
 
  //
  float thermistorResistance =
      SERIES_RESISTOR *
      (rawADC / (1023.0 - rawADC));

  // Beta-model thermistor equation.
  float steinhart =
      log(thermistorResistance / R0) / B_COEFF;

  steinhart += 1.0 / T0;

  // Convert Kelvin to Celsius.
  float temperatureC =
      (1.0 / steinhart) - 273.15;

  return temperatureC;
}


// --------------------------------------------------
// Check the software temperature safety limit
// --------------------------------------------------
void checkTemperatureSafety(float temperatureC) {

  // ------------------------------------------------
  // Temperature TOO HIGH
  // ------------------------------------------------
  if (temperatureC > TEMPERATURE_LIMIT_C) {

    // Only print the shutdown message the first time
    // the limit is crossed.
    if (!safetyShutdown) {

      safetyShutdown = true;

      // Set requested PWM to zero.
      pwmValue = 0;

      // Immediately shut down BOTH H-bridge inputs.
      analogWrite(HBRIDGE_PIN9, 0);
      analogWrite(HBRIDGE_PIN10, 0);

      Serial.print("SAFETY SHUTDOWN ACTIVE: Temperature = ");
      Serial.print(temperatureC, 2);
      Serial.print(" C exceeds ");
      Serial.print(TEMPERATURE_LIMIT_C, 1);
      Serial.println(" C. Both PWM outputs forced to 0.");
    }

  }

  // ------------------------------------------------
  // Temperature has returned below the limit
  // ------------------------------------------------
  else {

    if (safetyShutdown) {

      safetyShutdown = false;

      // Keep the TEC OFF after a shutdown.
      // The user must send a new command before
      // the TEC is allowed to run again.
      pwmValue = 0;

      analogWrite(HBRIDGE_PIN9, 0);
      analogWrite(HBRIDGE_PIN10, 0);

      Serial.println(
        "SAFETY LIMIT CLEARED: PWM remains 0 until a new command."
      );
    }
  }
}


// --------------------------------------------------
// Process one command from the Python GUI
// --------------------------------------------------
void processCommand() {

  int requestedPwm;
  char requestedDirection[6];

  // Accept exactly the command format sent by the
  // Python GUI:
  //
  // SET PWM 120 DIR HEAT
  //
  if (sscanf(
        commandBuffer,
        "SET PWM %d DIR %5s",
        &requestedPwm,
        requestedDirection
      ) != 2) {

    Serial.print("ERROR: Invalid command: ");
    Serial.println(commandBuffer);

    // Fail safe if an invalid command is received.
    pwmValue = 0;
    analogWrite(HBRIDGE_PIN9, 0);
    analogWrite(HBRIDGE_PIN10, 0);

    return;
  }


  // ------------------------------------------------
  // Determine direction first.
  // ------------------------------------------------
  if (strcmp(requestedDirection, "HEAT") == 0) {

    heating = true;

  } else if (strcmp(requestedDirection, "COOL") == 0) {

    heating = false;

  } else {

    Serial.println("ERROR: Direction must be HEAT or COOL.");

    // Fail safe for invalid direction.
    pwmValue = 0;
    analogWrite(HBRIDGE_PIN9, 0);
    analogWrite(HBRIDGE_PIN10, 0);

    return;
  }


  // ------------------------------------------------
  // Keep PWM in legal analogWrite range.
  // ------------------------------------------------
  pwmValue = constrain(requestedPwm, 0, 255);


  // ------------------------------------------------
  // If safety shutdown is active, don't allow the
  // command to restart the TEC.
  // ------------------------------------------------
  if (safetyShutdown) {

    pwmValue = 0;

    analogWrite(HBRIDGE_PIN9, 0);
    analogWrite(HBRIDGE_PIN10, 0);

    Serial.println(
      "COMMAND BLOCKED: Safety shutdown is active; PWM remains 0."
    );

    return;
  }


  // ------------------------------------------------
  // Apply the new command.
  // ------------------------------------------------
  applyTecOutput();

  Serial.print("COMMAND ACCEPTED: SET PWM ");
  Serial.print(pwmValue);
  Serial.print(" DIR ");
  Serial.println(heating ? "HEAT" : "COOL");
}


// --------------------------------------------------
// Read serial commands
// --------------------------------------------------
void readSerialCommands() {

  // Read available characters without delay(),
  // so slider movement is applied promptly.

  while (Serial.available() > 0) {

    char incoming = Serial.read();

    if (incoming == '\r') {
      continue;
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

      // Drop an overlong command rather than writing
      // past the end of the buffer.

      commandLength = 0;

      pwmValue = 0;

      analogWrite(HBRIDGE_PIN9, 0);
      analogWrite(HBRIDGE_PIN10, 0);

      Serial.println(
        "ERROR: Command too long. Both PWM outputs forced to 0."
      );
    }
  }
}


// --------------------------------------------------
// Report telemetry
// --------------------------------------------------
void reportTelemetry(float temperatureC) {

  // The Python program parses this line for its
  // readouts, plot, and CSV file.
  //
  // IMPORTANT:
  // The original telemetry format is preserved so
  // P5_Manual_heat_cool_display.py can continue
  // parsing it.

  Serial.print("Temperature (C): ");
  Serial.print(temperatureC, 2);

  Serial.print(", Time (s): ");
  Serial.print(millis() / 1000.0, 2);

  Serial.print(", PWM: ");
  Serial.print(pwmValue);

  Serial.print(", DIR: ");
  Serial.println(heating ? "HEAT" : "COOL");
}


// --------------------------------------------------
// Setup
// --------------------------------------------------
void setup() {

  Serial.begin(9600);

  pinMode(HBRIDGE_PIN9, OUTPUT);
  pinMode(HBRIDGE_PIN10, OUTPUT);

  // Start with both H-bridge inputs OFF.
  pwmValue = 0;

  analogWrite(HBRIDGE_PIN9, 0);
  analogWrite(HBRIDGE_PIN10, 0);
}


// --------------------------------------------------
// Main loop
// --------------------------------------------------
void loop() {

  // Check for commands from the Python GUI.
  readSerialCommands();


  // ------------------------------------------------
  // Read temperature.
  //
  // readTemperatureC() averages 500 ADC readings.
  // ------------------------------------------------
  float temperatureC = readTemperatureC();


  // ------------------------------------------------
  // Check the 60 C safety limit.
  // ------------------------------------------------
  checkTemperatureSafety(temperatureC);


  // ------------------------------------------------
  // Re-apply the output after the safety check.
  //
  // If safetyShutdown == true, this keeps both
  // outputs at zero.
  // ------------------------------------------------
  applyTecOutput();


  // ------------------------------------------------
  // Send telemetry twice per second.
  //
  // Telemetry continues even during a safety shutdown.
  // ------------------------------------------------
  if (millis() - lastReportMs >= 500) {

    lastReportMs = millis();

    reportTelemetry(temperatureC);
  }
}
```
