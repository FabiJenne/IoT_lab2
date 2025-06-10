/*
 BLE_led.ino Simple BLE example to control the led
*/


// Libraries

#include <ArduinoBLE.h>

// Define a service
BLEService ledService("19B10000-E8F2-537E-4F6C-D104768A1214");  

// BLE LED Switch Characteristic - custom 128-bit UUID, read and writable by central
BLEByteCharacteristic switchCharacteristic("19B10001-E8F2-537E-4F6C-D104768A1214", BLERead | BLEWrite);

// pin to use for the LED
const int ledPin = LED_BUILTIN; 

void setup() {
  Serial.begin(9600);
  while (!Serial);

  // set LED pin to output mode
  pinMode(ledPin, OUTPUT);

  // begin initialization
  if (!BLE.begin()) {
    Serial.println("starting BLE failed!");

    while (1);
  }


// set advertised local name and service UUID:
  BLE.setLocalName("BLE-LAB55");
  BLE.setAdvertisedService(ledService);

// add the characteristic to the service
  ledService.addCharacteristic(switchCharacteristic);
  
// add service
  BLE.addService(ledService);

  // set the initial value for the characeristic:
  switchCharacteristic.writeValue(0);

  // start advertising
  BLE.advertise();

  Serial.println("BLE LED Peripheral");
}

void loop() {
  // listen for BLE peripherals to connect:
  BLEDevice central = BLE.central();

  // if a central is connected to peripheral:
  if (central) {
    Serial.print("Connected to central: ");
    // print the central's MAC address (not important when using BLE)
    Serial.println(central.address());
  
    // while the central is still connected to peripheral:
    while (central.connected()) {
      // if the remote device wrote to the characteristic,
      // use the value to control the LED:
      if (switchCharacteristic.written()) 
      {
        if (switchCharacteristic.value()) 
        {   
          // any value other than 0
          Serial.println("LED on");
          Serial.println(switchCharacteristic.value());

           // will turn the LED on
          digitalWrite(ledPin, HIGH);        
        } 
        else 
        {                              
          // If a 0 is written
          Serial.println(F("LED off"));

          // will turn the LED off
          digitalWrite(ledPin, LOW);          
        }
      }    
    }

    // when the central disconnects, print it out:
    Serial.print(F("Disconnected from central: "));
    Serial.println(central.address());
  }
}
