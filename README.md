

# CarConnectivity Plugin for ABRP - A Better Routeplanner
[![GitHub sourcecode](https://img.shields.io/badge/Source-GitHub-green)](https://github.com/tillsteinbach/CarConnectivity-plugin-abrp/)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/tillsteinbach/CarConnectivity-plugin-abrp)](https://github.com/tillsteinbach/CarConnectivity-plugin-abrp/releases/latest)
[![GitHub](https://img.shields.io/github/license/tillsteinbach/CarConnectivity-plugin-abrp)](https://github.com/tillsteinbach/CarConnectivity-plugin-abrp/blob/master/LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/tillsteinbach/CarConnectivity-plugin-abrp)](https://github.com/tillsteinbach/CarConnectivity-plugin-abrp/issues)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/carconnectivity-plugin-abrp?label=PyPI%20Downloads)](https://pypi.org/project/carconnectivity-plugin-abrp/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/carconnectivity-plugin-abrp)](https://pypi.org/project/carconnectivity-plugin-abrp/)
[![Donate at PayPal](https://img.shields.io/badge/Donate-PayPal-2997d8)](https://www.paypal.com/donate?hosted_button_id=2BVFF5GJ9SXAJ)
[![Sponsor at Github](https://img.shields.io/badge/Sponsor-GitHub-28a745)](https://github.com/sponsors/tillsteinbach)

[CarConnectivity](https://github.com/tillsteinbach/CarConnectivity) is a python API to connect to various car services. If you want to automatically forward the data collected from your vehicle to [A Better Routeplanner (ABRP)[https://abetterrouteplanner.com) this plugin will help you.

## Configuration
In your carconnectivity.json configuration add a section for the abrp plugin like this:
```
{
    "carConnectivity": {
        "connectors": [
            ...
        ]
        "plugins": [
            {
                "type": "abrp",
                "config": {
                    "tokens": {
                        "TMBLJ9NY8SF000000": "1623fdc3-4aaf-49f5-b51a-1e55435435da2",
                        "TMLLJ9NY23F000000": "12afe123-59d4-8a3d-b9ef-29367de7f8749"
                    }
                }
            }
        ]
    }
}
```
To retrieve your token go to your vehicle on [A Better Routeplanner (ABRP)[https://abetterrouteplanner.com) select "Live Data" and then link your vehicle using the "Generic" section. It will display you the token to paste in the configuration. You need to configure a mapping between the VIN and the token for each vehicle you want to connect to [ABRP[https://abetterrouteplanner.com)