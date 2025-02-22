# CarConnectivity Plugin for ABRP Config Options
The configuration for CarConnectivity is a .json file.
## General format
The general format is a `carConnectivity` section, followed by a list of connectors and plugins.
In the `carConnectivity` section you can set the global `log_level`.
Each connector or plugin needs a `type` attribute and a `config` section.
The `type` and config options specific to your connector or plugin can be found on their respective project page.
```json
{
    "carConnectivity": {
        "log_level": "error", // set the global log level, you can set individual log levels in the connectors and plugins
        "connectors": [
            {
                "type": "skoda", // Definition for a MySkoda account
                "config": {
                    "interval": 600, // Interval in which the server is checked in seconds
                    "username": "test@test.de", // Username of your MySkoda Account
                    "password": "testpassword123" // Password of your MySkoda Account
                }
            },
            {
                "type": "volkswagen", // Definition for a Volkswagen account
                "config": {
                    "interval": 300, // Interval in which the server is checked in seconds
                    "username": "test@test.de", // Username of your Volkswagen Account
                    "password": "testpassword123" // Username of your Volkswagen Account
                }
            }
        ],
        "plugins": [
            {
                "type": "abrp", // Minimal definition for the ABRP Connection
                "config": {
                    "tokens": { // Token mapping
                        "HEPFLJ9NY8SF098455": "16234fec3-4aa3e-4723e-b51f-1e5e37h4755da3"
                    }
                }
            }
        ]
    }
}
```
### ABRP Plugin Options
These are the valid options for the ABRP plugin
```json
{
    "carConnectivity": {
        "connectors": [],
        "plugins": [
            {
                "type": "abrp", // Definition for the ABRP plugin
                "disabled": false, // You can disable plugins without removing them from the config completely
                "config": {
                    "log_level": "error", // The log level for the plugin. Otherwise uses the global log level
                    "tokens": { // Token mapping one line for each car, key is the VIN, value is the ABRP token for the car
                        "HEPFLJ9NY8SF098455": "16234fec3-4aa3e-4723e-b51f-1e5e37h4755da3", // First car
                        "H34FLJ9NS8SF095654": "66225132f4-8afeea-1323e-b51f-1e53455dfe31", // Second car
                    },
                    "interval": 30, // Interval to send data to ABRP (this should be reasonably low to not stress the server)
                }
            }
        ]
    }
}
```

### Connector Options
Valid Options for connectors can be found here:
* [CarConnectivity-connector-skoda Config Options](https://github.com/tillsteinbach/CarConnectivity-connector-skoda/tree/main/doc/Config.md)
* [CarConnectivity-connector-volkswagen Config Options](https://github.com/tillsteinbach/CarConnectivity-connector-volkswagen/tree/main/doc/Config.md)
* [CarConnectivity-connector-seatcupra Config Options](https://github.com/tillsteinbach/CarConnectivity-connector-seatcupra/tree/main/doc/Config.md)
* [CarConnectivity-connector-tronity Config Options](https://github.com/tillsteinbach/CarConnectivity-connector-tronity/tree/main/doc/Config.md)
