#include <ESP8266WiFi.h>
#include <espnow.h>

const int VIBRATOR_RIGHT = D2;  // Vibrator for "right"
const int VIBRATOR_LEFT = D1;   // Vibrator for "left"

// Define the MAC addresses of both devices
uint8_t device1MAC[] = {0x24, 0x4C, 0xAB, 0x51, 0xa9, 0x33};  // MAC address of device 1
uint8_t device2MAC[] = {0x24, 0x4C, 0xAB, 0x51, 0x86, 0x9E};  // MAC address of device 2

// Structure to hold the message data
typedef struct struct_message {
    char message[32];  // Buffer for message
} struct_message;

struct_message dataToSend, receivedData;

// Callback function to handle received data
void OnDataRecv(uint8_t *mac_addr, uint8_t *incomingData, uint8_t len) {
    memcpy(&receivedData, incomingData, sizeof(receivedData));
    String receivedMessage = String(receivedData.message);
    receivedMessage.trim();

    Serial.print("Received: ");
    Serial.println(receivedMessage);

    if (receivedMessage == "R") {
        Serial.println("Activating Right Vibrator...");
        digitalWrite(VIBRATOR_RIGHT, HIGH);
        delay(400);
        digitalWrite(VIBRATOR_RIGHT, LOW);
    } else if (receivedMessage == "L") {
        Serial.println("Activating Left Vibrator...");
        digitalWrite(VIBRATOR_LEFT, HIGH);
        delay(400);
        digitalWrite(VIBRATOR_LEFT, LOW);
    } else if (receivedMessage == "S") {
        Serial.println("STOP");
        digitalWrite(VIBRATOR_LEFT, HIGH);
        digitalWrite(VIBRATOR_RIGHT, HIGH);
        delay(800);
        digitalWrite(VIBRATOR_LEFT, LOW);
        digitalWrite(VIBRATOR_RIGHT, LOW);
    }
}

// Callback function to handle sent data status
void OnDataSent(uint8_t *mac_addr, uint8_t sendStatus) {
    Serial.print("Last Packet Send Status: ");
    if (sendStatus == 0) {
        Serial.println("Delivery success");
    } else {
        Serial.println("Delivery fail");
    }
}

void setup() {
    Serial.begin(115200);
    WiFi.mode(WIFI_STA);  // Set ESP8266 to station mode

    pinMode(VIBRATOR_RIGHT, OUTPUT);
    pinMode(VIBRATOR_LEFT, OUTPUT);
    digitalWrite(VIBRATOR_RIGHT, LOW);
    digitalWrite(VIBRATOR_LEFT, LOW);

    if (esp_now_init() != 0) {
        Serial.println("ESP-NOW Init Failed");
        return;
    }

    esp_now_set_self_role(ESP_NOW_ROLE_COMBO);  // Set device as both sender and receiver
    esp_now_register_recv_cb(OnDataRecv);
    esp_now_register_send_cb(OnDataSent);

    // Add the other device as a peer
    esp_now_add_peer(device1MAC, ESP_NOW_ROLE_SLAVE, 1, NULL, 0);
    esp_now_add_peer(device2MAC, ESP_NOW_ROLE_SLAVE, 1, NULL, 0);

    Serial.println("ESP-NOW Initialized");
}

void loop() {
    // Send data to device 1
    if (Serial.available()) {
        String input = Serial.readStringUntil('\n');
        input.trim();
        input.toCharArray(dataToSend.message, sizeof(dataToSend.message));

        Serial.print("Sending to Device 1: ");
        Serial.println(dataToSend.message);

        esp_now_send(device1MAC, (uint8_t *)&dataToSend, sizeof(dataToSend));
        delay(100);
    }

    // Send data to device 2
    if (Serial.available()) {
        String input = Serial.readStringUntil('\n');
        input.trim();
        input.toCharArray(dataToSend.message, sizeof(dataToSend.message));

        Serial.print("Sending to Device 2: ");
        Serial.println(dataToSend.message);

        esp_now_send(device2MAC, (uint8_t *)&dataToSend, sizeof(dataToSend));
        delay(100);
    }
}