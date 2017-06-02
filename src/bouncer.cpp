#include "Arduino.h"

#define serial_baud 115200 // Serial Baud rate.
#define testPin 2  // Pin where the switch under test is connected
#define ledPin 13  // Pin where a led goes to show if it's active or not.
#define samples_count 200 // Number of samples to track.
#define settle_time 200000 // Microseconds to wait before the end of a bounce

uint8_t start_state;
volatile unsigned long events[samples_count];
volatile int event_nr;

void send_bounce_data() {
    uint8_t state = start_state;
    unsigned long start_moment = events[0];
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
    Serial.println(digitalRead(testPin));
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
    attachInterrupt(digitalPinToInterrupt(testPin), bounce, CHANGE);
    Serial.println("READY");
}

void loop() {
    if(event_nr != 0 && (events[event_nr] + settle_time) < micros()) {
        // Not seen new events for settle_time. we're done.
        send_bounce_data();
        cleanup();
        start_state = digitalRead(testPin);
    }
}
