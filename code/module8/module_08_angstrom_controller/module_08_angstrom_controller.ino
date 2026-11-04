// Module 8: Angstrom boundary drive. T_set(t) = Ta + Tb sin(phase) with OPEN / P / PI control.
// Copy of the Module 7 sketch; that file is unchanged. Control now runs here, not in Python.
// The GUI sends the schedule and a heartbeat; the Arduino validates and runs the schedule.
// Only the TEC thermistor (A1) enters feedback. Baud: 115200.
//
// Commands (one per line). A malformed command stops the run with output zero.
//   PING                        heartbeat; a run stops if none arrives for 2 s
//   MODE OPEN|P|PI              select control mode (not during a run)
//   GAINS <Kp> <Ki>             PWM/C and PWM/(C s) (not during a run)
//   RATIO <r>                   cooling multiplier r = chi_h/chi_c (not during a run)
//   LIMIT <pwm>                 PWM saturation, 1-255 (not during a run)
//   CLEAR                       empty the schedule (not during a run)
//   STEP <dur_s> <Ta> <Tb> <period_s>   append a schedule step (not during a run)
//   START                       begin the schedule
//   STOP                        end the run, output zero
//
// Every record has 18 fields (header printed at startup). "nan" is the placeholder
// for fields that do not apply. Other lines start with EVENT.
//   run_state: IDLE RUN DONE STOPPED SHUTDOWN SENSOR_FAULT ROD_LIMIT TIMEOUT
//   control_mode: OPEN P PI
//   T1_C..T5_C are the rod sensors in hole order; T5_C is the sensor with wire tag T6.
#include <Arduino.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

// Report order: TEC, rod1 (nearest TEC) ... rod5. Pins follow the bench wiring.
const byte SENSOR_COUNT = 6;
const byte TEC_SENSOR = 0;
const byte ROD_BASE_SENSOR = 1;
const int THERMISTOR_PINS[SENSOR_COUNT] = {A1, A5, A4, A3, A2, A0};
const int HEAT_PIN = 9;
const int COOL_PIN = 10;
// Same divider and Beta-model constants as Module 4.
const float SERIES_RESISTOR = 100000.0;
const float R0 = 100000.0;
const float B_COEFF = 3950.0;
const float T0 = 298.15;
const int TEMPERATURE_SAMPLES = 1000;
const float TEMPERATURE_LIMIT_C = 60.0;  // TEC thermistor, as in Modules 4-7.
const float ROD_BASE_LIMIT_C = 56.0;     // Lab-09: measured rod-base (T1) limit.
const float MIN_SETPOINT_C = 10.0;       // Lowest temperature in the Module 4 table.
const float MIN_PERIOD_S = 100.0;        // Lab-09: never use a shorter period.
const unsigned long COMMAND_TIMEOUT_MS = 2000;
const byte MAX_STEPS = 8;

// Module 4 steady-state curve T_ss = f(u), as temperature (C) and signed PWM.
// The last point extends the heating branch to 56 C with chi_h = 0.5311 C/count.
const byte FF_POINTS = 10;
const float FF_TEMP[FF_POINTS] = {10.05, 13.365, 16.415, 19.575, 21.965, 28.14, 33.55, 38.905, 45.0, 56.0};
const float FF_PWM[FF_POINTS] = {-63, -47, -31, -13, 0, 11, 21, 32, 43, 63.7};

enum RunState { IDLE, RUNNING, DONE, STOPPED, SHUTDOWN, SENSOR_FAULT, ROD_LIMIT, TIMED_OUT };
enum ControlMode { MODE_OPEN, MODE_P, MODE_PI };
struct Step { float duration; float ta; float tb; float period; };

RunState runState = IDLE;
ControlMode controlMode = MODE_PI;
Step steps[MAX_STEPS];
byte stepCount = 0;
byte currentStep = 0;
float kp = 16.0;
float ki = 0.5;
float ratioR = 2.83;  // Module 4 fit, chi_h/chi_c.
int pwmLimit = 255;

float phase = 0.0;
float stepElapsed = 0.0;
float integralQ = 0.0;
float setpointC = NAN;
float feedforwardPwm = NAN;
float controllerPwm = NAN;
int signedPwm = 0;
unsigned long lastControlMs = 0;
unsigned long lastCommandMs = 0;
unsigned long lastByteMs = 0;
char commandBuffer[48];
byte commandLength = 0;
bool discardCommand = false;

bool running() { return runState == RUNNING; }

void stopOutput() {
  signedPwm = 0;
  analogWrite(HEAT_PIN, 0);
  analogWrite(COOL_PIN, 0);
}

void applyOutput() {
  if (!running()) {
    stopOutput();
    return;
  }
  // Clear the opposite output BEFORE enabling the selected output.
  if (signedPwm >= 0) {
    analogWrite(COOL_PIN, 0);
    analogWrite(HEAT_PIN, signedPwm);
  } else {
    analogWrite(HEAT_PIN, 0);
    analogWrite(COOL_PIN, -signedPwm);
  }
}

const char *stateName() {
  switch (runState) {
    case RUNNING: return "RUN";
    case DONE: return "DONE";
    case STOPPED: return "STOPPED";
    case SHUTDOWN: return "SHUTDOWN";
    case SENSOR_FAULT: return "SENSOR_FAULT";
    case ROD_LIMIT: return "ROD_LIMIT";
    case TIMED_OUT: return "TIMEOUT";
    default: return "IDLE";
  }
}

const char *modeName() {
  if (controlMode == MODE_OPEN) return "OPEN";
  return controlMode == MODE_P ? "P" : "PI";
}

void printEventHead(const __FlashStringHelper *name) {
  Serial.print(F("EVENT,")); Serial.print(millis()); Serial.print(',');
  Serial.print(name);
}

// Every path out of a run comes here, so the output always ends at zero.
void endRun(RunState reason) {
  bool wasRunning = running();
  runState = reason;
  stopOutput();
  setpointC = NAN;
  feedforwardPwm = NAN;
  controllerPwm = NAN;
  if (wasRunning) {
    printEventHead(F("END,")); Serial.println(stateName());
  }
}

void reject(const __FlashStringHelper *why) {
  printEventHead(F("REJECT,")); Serial.println(why);
  if (running()) endRun(STOPPED);
}

// Average the same 1000 ADC readings per sensor, then convert once.
// Discard one conversion after changing channels to settle the multiplexed ADC.
float readTemperatureC(int pin) {
  analogRead(pin);
  unsigned long sum = 0;
  for (int i = 0; i < TEMPERATURE_SAMPLES; ++i) {
    sum += analogRead(pin);
  }
  float averageADC = (float)sum / TEMPERATURE_SAMPLES;
  if (averageADC <= 0.0 || averageADC >= 1023.0) return NAN;
  float resistance = SERIES_RESISTOR * averageADC / (1023.0 - averageADC);
  float inverseT = log(resistance / R0) / B_COEFF + 1.0 / T0;
  return 1.0 / inverseT - 273.15;
}

// Linear interpolation of the inverse curve u_ff = f^-1(T_set), clamped at the table ends.
float feedforwardFor(float temperature) {
  if (temperature <= FF_TEMP[0]) return FF_PWM[0];
  for (byte i = 1; i < FF_POINTS; ++i) {
    if (temperature <= FF_TEMP[i]) {
      float fraction = (temperature - FF_TEMP[i - 1]) / (FF_TEMP[i] - FF_TEMP[i - 1]);
      return FF_PWM[i - 1] + fraction * (FF_PWM[i] - FF_PWM[i - 1]);
    }
  }
  return FF_PWM[FF_POINTS - 1];
}

// The sign chooses direction. Negative commands get the multiplier r BEFORE saturation.
float compensated(float raw) { return raw < 0 ? ratioR * raw : raw; }

void printStepEvent() {
  printEventHead(F("STEP,"));
  Serial.print(currentStep + 1); Serial.print(',');
  Serial.print(steps[currentStep].duration, 1); Serial.print(',');
  Serial.print(steps[currentStep].ta, 2); Serial.print(',');
  Serial.print(steps[currentStep].tb, 2); Serial.print(',');
  Serial.println(steps[currentStep].period, 1);
}

void updateControl(float tecC, unsigned long nowMs) {
  float dt = (nowMs - lastControlMs) / 1000.0;
  lastControlMs = nowMs;
  stepElapsed += dt;
  while (stepElapsed >= steps[currentStep].duration) {
    stepElapsed -= steps[currentStep].duration;
    if (++currentStep >= stepCount) {
      currentStep = stepCount - 1;
      endRun(DONE);
      return;
    }
    printStepEvent();
  }
  const Step &step = steps[currentStep];
  // One running phase: changing the period changes its rate, so the setpoint cannot jump.
  phase += 2.0 * PI * dt / step.period;
  if (phase >= 2.0 * PI) phase -= 2.0 * PI;
  setpointC = step.ta + step.tb * sin(phase);

  float command;
  if (controlMode == MODE_OPEN) {
    feedforwardPwm = feedforwardFor(setpointC);
    controllerPwm = NAN;
    command = feedforwardPwm;
  } else {
    feedforwardPwm = NAN;
    float error = setpointC - tecC;
    float raw = kp * error;
    if (controlMode == MODE_PI) {
      float proposedQ = integralQ + error * dt;
      float proposed = compensated(raw + ki * proposedQ);
      // Conditional anti-windup, as in pi_logic.py: hold q if it pushes further past the limit.
      bool farther = (proposed > pwmLimit && error > 0) || (proposed < -pwmLimit && error < 0);
      if (!farther) integralQ = proposedQ;
      raw += ki * integralQ;
    }
    controllerPwm = raw;
    command = compensated(raw);
  }
  signedPwm = (int)lround(constrain(command, (float)-pwmLimit, (float)pwmLimit));
}

// Rod-base stop: lab-09 limit. It only ends a run; it never drives the output.
void checkRodBase(float temperature) {
  if (!running()) return;
  if (!isfinite(temperature) || temperature > ROD_BASE_LIMIT_C) endRun(ROD_LIMIT);
}

void checkTec(float temperature) {
  if (!isfinite(temperature)) endRun(SENSOR_FAULT);
  else if (temperature > TEMPERATURE_LIMIT_C) endRun(SHUTDOWN);
  else if (runState == SENSOR_FAULT || runState == SHUTDOWN) runState = IDLE;  // Needs a new START.
}

bool readFloats(const char *text, float values[], byte count) {
  char *end = (char *)text;
  for (byte i = 0; i < count; ++i) {
    const char *start = end;
    values[i] = strtod(start, &end);
    if (end == start || !isfinite(values[i])) return false;
  }
  return *end == '\0';
}

void startRun() {
  if (stepCount == 0) { reject(F("no schedule")); return; }
  if (runState == SHUTDOWN || runState == SENSOR_FAULT) { reject(F("TEC not safe")); return; }
  runState = RUNNING;
  currentStep = 0;
  phase = 0.0;
  stepElapsed = 0.0;
  integralQ = 0.0;
  lastControlMs = millis();
  printEventHead(F("START,"));
  Serial.print(modeName()); Serial.print(',');
  Serial.print(kp, 3); Serial.print(',');
  Serial.print(ki, 4); Serial.print(',');
  Serial.print(ratioR, 3); Serial.print(',');
  Serial.println(pwmLimit);
  printStepEvent();
}

void processCommand() {
  // Parse strictly; reject trailing junk, missing values, or unknown words.
  float v[4];
  if (strcmp(commandBuffer, "PING") == 0) {
    lastCommandMs = millis();
    return;
  }
  if (strcmp(commandBuffer, "STOP") == 0) {
    lastCommandMs = millis();
    if (running()) endRun(STOPPED);
    return;
  }
  if (strcmp(commandBuffer, "START") == 0) {
    lastCommandMs = millis();
    if (!running()) startRun();
    return;
  }
  if (running()) { reject(F("busy")); return; }
  lastCommandMs = millis();
  if (strcmp(commandBuffer, "CLEAR") == 0) {
    stepCount = 0;
  } else if (strcmp(commandBuffer, "MODE OPEN") == 0) {
    controlMode = MODE_OPEN;
  } else if (strcmp(commandBuffer, "MODE P") == 0) {
    controlMode = MODE_P;
  } else if (strcmp(commandBuffer, "MODE PI") == 0) {
    controlMode = MODE_PI;
  } else if (strncmp(commandBuffer, "GAINS ", 6) == 0) {
    if (!readFloats(commandBuffer + 6, v, 2) || v[0] < 0 || v[1] < 0) { reject(F("gains")); return; }
    kp = v[0]; ki = v[1];
  } else if (strncmp(commandBuffer, "RATIO ", 6) == 0) {
    if (!readFloats(commandBuffer + 6, v, 1) || v[0] <= 0) { reject(F("ratio")); return; }
    ratioR = v[0];
  } else if (strncmp(commandBuffer, "LIMIT ", 6) == 0) {
    if (!readFloats(commandBuffer + 6, v, 1) || v[0] < 1 || v[0] > 255) { reject(F("limit")); return; }
    pwmLimit = (int)v[0];
  } else if (strncmp(commandBuffer, "STEP ", 5) == 0) {
    if (!readFloats(commandBuffer + 5, v, 4)) { reject(F("step format")); return; }
    if (stepCount >= MAX_STEPS) { reject(F("too many steps")); return; }
    if (v[0] <= 0 || v[2] < 0 || v[3] < MIN_PERIOD_S ||
        v[1] + v[2] > ROD_BASE_LIMIT_C || v[1] - v[2] < MIN_SETPOINT_C) {
      reject(F("step limits"));
      return;
    }
    steps[stepCount++] = {v[0], v[1], v[2], v[3]};
  } else {
    reject(F("unknown command"));
  }
}

void readCommands() {
  // Nonblocking, bounded work: a partial command never delays temperature checks.
  if (commandLength > 0 && millis() - lastByteMs > 1000) {
    if (running()) endRun(STOPPED);
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
      if (running()) endRun(STOPPED);
      commandLength = 0;
      discardCommand = true;
    } else {
      commandBuffer[commandLength++] = incoming;
    }
  }
}

void serviceCommands() {
  readCommands();
  if (running() && millis() - lastCommandMs > COMMAND_TIMEOUT_MS) endRun(TIMED_OUT);
  applyOutput();
}

void printValue(float value, byte digits) {
  if (isfinite(value)) Serial.print(value, digits);
  else Serial.print(F("nan"));  // Keep the record structure for fields that do not apply.
}

// One complete record per six-channel acquisition, including during shutdown.
void report(const float temperatures[], unsigned long acquisitionMs) {
  bool active = running();
  const Step &step = steps[currentStep];
  Serial.print(acquisitionMs); Serial.print(',');
  Serial.print(stateName()); Serial.print(',');
  Serial.print(modeName()); Serial.print(',');
  Serial.print(active ? currentStep + 1 : 0); Serial.print(',');
  printValue(active ? step.ta : NAN, 2); Serial.print(',');
  printValue(active ? step.tb : NAN, 2); Serial.print(',');
  printValue(active ? step.period : NAN, 1); Serial.print(',');
  printValue(setpointC, 3); Serial.print(',');
  printValue(feedforwardPwm, 2); Serial.print(',');
  for (byte channel = 0; channel < SENSOR_COUNT; ++channel) {
    printValue(temperatures[channel], 2); Serial.print(',');
  }
  printValue(controllerPwm, 2); Serial.print(',');
  printValue(active && controlMode != MODE_OPEN ? ratioR : NAN, 3); Serial.print(',');
  Serial.println(signedPwm);
}

void setup() {
  Serial.begin(115200);
  pinMode(HEAT_PIN, OUTPUT);
  pinMode(COOL_PIN, OUTPUT);
  stopOutput();
  Serial.println(F("time_ms,run_state,control_mode,step,Ta_C,Tb_C,period_s,setpoint_C,feedforward_pwm,"
                   "TEC_C,T1_C,T2_C,T3_C,T4_C,T5_C,controller_pwm,heating_to_cooling_ratio,signed_pwm"));
}

void loop() {
  float temperatures[SENSOR_COUNT];
  // Check the TEC sensor before processing any command that could enable output.
  temperatures[TEC_SENSOR] = readTemperatureC(THERMISTOR_PINS[TEC_SENSOR]);
  checkTec(temperatures[TEC_SENSOR]);
  serviceCommands();

  // Commands and timeouts are serviced between rod-channel measurements.
  for (byte channel = 1; channel < SENSOR_COUNT; ++channel) {
    temperatures[channel] = readTemperatureC(THERMISTOR_PINS[channel]);
    if (channel == ROD_BASE_SENSOR) checkRodBase(temperatures[channel]);
    serviceCommands();
  }
  unsigned long acquisitionMs = millis();
  if (running()) {
    updateControl(temperatures[TEC_SENSOR], acquisitionMs);
    applyOutput();
  }
  report(temperatures, acquisitionMs);
}
