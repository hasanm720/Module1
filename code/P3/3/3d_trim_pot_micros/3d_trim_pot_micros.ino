#include <math.h>

void setup() {
  Serial.begin(9600);
  Serial.println("Starting experiment...");
}

void loop() {

  int Nsequential_steps = 100;
  int average_timescale = 1000;
  float vref = 5.0;

  float unaveraged[100];
  float averaged[100];

  // Variable to store timing result
  unsigned long elapsedTime = 0;


  // -------------------------------
  // FIRST: 100 UNAVERAGED VALUES
  // -------------------------------

  Serial.println("Starting unaveraged measurements...");

  for (int i = 0; i < Nsequential_steps; i++) {

    float sensorValue = analogRead(A0);
    float voltageValue = vref * (sensorValue / 1023.0);

    unaveraged[i] = voltageValue;

    Serial.print("Unaveraged ");
    Serial.print(i);
    Serial.print(": ");
    Serial.println(voltageValue, 4);

    delay(1);
  }

  Serial.println("Finished unaveraged measurements.");


  // -------------------------------
  // SECOND: 100 AVERAGED VALUES
  // -------------------------------

  Serial.println("Starting averaged measurements...");

  for (int i = 0; i < Nsequential_steps; i++) {

    float sensor_value_sum = 0;

    // START TIMER
    unsigned long startTime = micros();

    // Acquire 1000 readings
    for (int j = 0; j < average_timescale; j++) {

      float sensorValue = analogRead(A0);

      sensor_value_sum += sensorValue;
    }

    // STOP TIMER
    unsigned long endTime = micros();

    // Calculate elapsed time
    elapsedTime = endTime - startTime;


    float average_sensor_value =
      sensor_value_sum / average_timescale;

    float voltageValue =
      vref * (average_sensor_value / 1023.0);

    averaged[i] = voltageValue;

    Serial.print("Averaged ");
    Serial.print(i);
    Serial.print(": ");
    Serial.println(voltageValue, 4);

    delay(1);
  }

  Serial.println("Finished averaged measurements.");


  // -------------------------------
  // CALCULATE MEANS
  // -------------------------------

  float sum1 = 0;
  float sum1000 = 0;

  for (int i = 0; i < Nsequential_steps; i++) {
    sum1 += unaveraged[i];
    sum1000 += averaged[i];
  }

  float mean1 = sum1 / Nsequential_steps;
  float mean1000 = sum1000 / Nsequential_steps;


  // -------------------------------
  // CALCULATE STANDARD DEVIATIONS
  // -------------------------------

  float squared_sum1 = 0;
  float squared_sum1000 = 0;

  for (int i = 0; i < Nsequential_steps; i++) {

    squared_sum1 +=
      (unaveraged[i] - mean1) *
      (unaveraged[i] - mean1);

    squared_sum1000 +=
      (averaged[i] - mean1000) *
      (averaged[i] - mean1000);
  }

  float s1 =
    sqrt(squared_sum1 / (Nsequential_steps - 1));

  float s1000 =
    sqrt(squared_sum1000 / (Nsequential_steps - 1));


  // -------------------------------
  // PRINT RESULTS
  // -------------------------------

  Serial.println();
  Serial.println("========== RESULTS ==========");

  Serial.print("Mean unaveraged = ");
  Serial.println(mean1, 6);

  Serial.print("s1 = ");
  Serial.println(s1, 6);

  Serial.print("Mean averaged = ");
  Serial.println(mean1000, 6);

  Serial.print("s1000 = ");
  Serial.println(s1000, 6);

  Serial.print("s1000/s1 = ");
  Serial.println(s1000 / s1, 6);

  Serial.print("1/sqrt(1000) = ");
  Serial.println(1.0 / sqrt(1000.0), 6);


  // -------------------------------
  // TIMING RESULTS
  // -------------------------------

  Serial.println();
  Serial.println("========== TIMING ==========");

  Serial.print("Elapsed time for 1000 analogRead() = ");
  Serial.print(elapsedTime);
  Serial.println(" microseconds");

  float conversionsPerSecond =
    1000000.0 / elapsedTime;

  Serial.print("analogRead() conversions/sec = ");
  Serial.println(conversionsPerSecond);

  float timePerConversion =
    elapsedTime / 1000.0;

  Serial.print("Time per conversion = ");
  Serial.print(timePerConversion);
  Serial.println(" microseconds");

  Serial.println("============================");


  // Don't repeat the experiment
  while (true) {
  }
}