#include <ArduinoBLE.h>
#include <Arduino_LSM6DS3.h>

#define BLE_UUID_SENSOR_DATA_SERVICE              "2BEEF31A-B10D-271C-C9EA-35D865C1F48A"
#define BLE_UUID_ACCEL_SENSOR_DATA                "4664E7A1-5A13-BFFF-4636-7D0A4B16496C"

#define NUMBER_OF_SENSORS 3

union multi_sensor_data{
  struct __attribute__( ( packed ) ) {
    float values[NUMBER_OF_SENSORS];
  };
  uint8_t bytes[ NUMBER_OF_SENSORS * sizeof( float ) ];
};

union multi_sensor_data accelSensorData;


//----------------------------------------------------------------------------------------------------------------------
// BLE
//----------------------------------------------------------------------------------------------------------------------

BLEService sensorDataService( BLE_UUID_SENSOR_DATA_SERVICE );
BLECharacteristic accelSensorDataCharacteristic( BLE_UUID_ACCEL_SENSOR_DATA, BLERead | BLENotify, sizeof accelSensorData.bytes );

const int BLE_LED_PIN = LED_BUILTIN;

//const int RSSI_LED_PIN = LED_PWR;

void setup(){
  Serial.begin( 9600 );
  //while ( !Serial );
 
if (!IMU.begin()){
  Serial.println("Failed lm6d3s accelerometer");
  while(1);
}

  pinMode( BLE_LED_PIN, OUTPUT );
 // pinMode( RSSI_LED_PIN, OUTPUT );

  if ( setupBleMode() )
  {
    digitalWrite( BLE_LED_PIN, HIGH );
  }


  for (int i = 0; i< NUMBER_OF_SENSORS; i++){
    accelSensorData.values[i] = 0.0;
  }
}

void loop()
{
  float x,y,z;
  #define UPDATE_INTERVALL 400
  static long previousMillis = 0;

  // listen for BLE peripherals to connect:
  BLEDevice central = BLE.central();

  if ( central )
  {
    Serial.print( "Connected to central: " );
    Serial.println( central.address() );

    while ( central.connected() )
    {
      unsigned long currentMillis = millis();
      if ( currentMillis - previousMillis > UPDATE_INTERVALL )
      {
        previousMillis = currentMillis;

        Serial.print( "Central RSSI: " );
        Serial.println( central.rssi() );

        if ( central.rssi() != 0 )
        {
          
    //      digitalWrite( RSSI_LED_PIN, LOW );

          if (IMU.accelerationAvailable()) {
            IMU.readAcceleration(x,y,z);
            accelSensorData.values[0] = x;
            accelSensorData.values[1] = y;
            accelSensorData.values[2] = z;
          }

          accelSensorDataCharacteristic.writeValue( accelSensorData.bytes, sizeof accelSensorData.bytes );
          
        }
      }
    }

    Serial.print( F( "Disconnected from central: " ) );
    Serial.println( central.address() );
  }
}

bool setupBleMode()
{
  if ( !BLE.begin() )
  {
    return false;
  }

  // set advertised local name and service UUID:
  BLE.setDeviceName( "BLE-LAB55" );
  BLE.setLocalName( "BLE-LAB55" );
  BLE.setAdvertisedService( sensorDataService );

  // BLE add characteristics
  sensorDataService.addCharacteristic( accelSensorDataCharacteristic );

  // add service
  BLE.addService( sensorDataService );

  // set the initial value for the characeristic:
  accelSensorDataCharacteristic.writeValue( accelSensorData.bytes, sizeof accelSensorData.bytes );

  // start advertising
  BLE.advertise();

  return true;
}