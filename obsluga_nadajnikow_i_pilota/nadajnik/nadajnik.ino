#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEBeacon.h>

#define DEVICE_NAME "BEACON_1" // Konfiguracja nazwy (BEACON_X)

void setup() {
  BLEDevice::init(DEVICE_NAME);
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID("4fafc201-1fb5-459e-8fcc-c5c9c331914b");
  pAdvertising->setScanResponse(true);
  BLEDevice::startAdvertising();
}

void loop() {
  delay(1000); // Nadajnik po prostu działa w tle
}