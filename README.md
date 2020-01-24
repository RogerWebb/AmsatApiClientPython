# Python Client for AMSAT Status and Passes APIs

## Usage

```
from amsat import AmsatApiClient

amsat = AmsatApiClient()

status = amsat.get_sat_status('AO-91', hours=24)
passes = amsat.get_sat_passes('CM85', 'AO-91')
```

## Command-Line Utility
The amsat-cli-py command-line utility is provided for convenience and a quick demonstration of how the API Client works.

### Get Status
```bash
python -m amsat-api-client-python status -n AO-91 -h 24
```

### Get Passes
```bash
python -m amsat-api-client-python passes -o AO-91 -l CM85
```
