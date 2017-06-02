#include "Arduino.h"

#define serial_baud 115200 // Serial Baud rate.
#define testPin 2  // Pin where the switch under test is connected
#define ledPin 13  // Pin where a led goes to show if it's active or not.
#define samples_count 100 // Number of samples to track.
#define settle_time 500000 // Microseconds to wait before the end of a bounce

uint8_t start_state;
unsigned long events[samples_count];
volatile int event_nr;

void send_bounce_data() {
    uint8_t state = start_state;
    long start_moment = events[0];
    Serial.print("START:");
    Serial.print(state);
    Serial.print(":");
    Serial.println(start_moment);
    for(int i=0; i<event_nr; i++) {
        Serial.print(i);
        Serial.print(":");
        Serial.print(state);
        Serial.print(":");
        Serial.println(events[i]-start_moment);
        state = !state;
    }
    Serial.print("END:");
    Serial.println(state);
}

void cleanup() {
    event_nr = 0;
    for(int i=0; i<samples_count; i++) {
        events[i] = 0;
    }
}

void bounce() {
    events[event_nr++] = micros();
}

void setup() {
    Serial.begin(serial_baud);
    pinMode(ledPin, OUTPUT);
    pinMode(testPin, INPUT);
    cleanup();
    start_state = digitalRead(testPin);
}

void loop() {
    if(event_nr == 0) {
        // The waiting for triggering state
        if(start_state != digitalRead(testPin)) {
            // The value changed!
            bounce();
            digitalWrite(ledPin, HIGH);
            attachInterrupt(digitalPinToInterrupt(testPin), bounce, CHANGE);
        }
    } else {
        // Actively Sampling bounces.
        if(events[event_nr] + settle_time < micros()) {
            // Not seen new events for settle_time. we're done.
            detachInterrupt(digitalPinToInterrupt(testPin));
            send_bounce_data();
            cleanup();
            digitalWrite(ledPin, LOW);
            start_state = digitalRead(testPin);
        }
    }
}
