# Python Client for AMSAT Status and Passes APIs

## Usage

```
from amsatapi import AmsatApiClient

amsat = AmsatApiClient()

status = amsat.get_sat_status('AO-91', hours=24)
passes = amsat.get_sat_passes('CM85', 'AO-91')
```

## Command-Line Utility
The command-line utility is provided for convenience and a quick demonstration of how the API Client works.

### Get Status
```bash
python -m amsatapi status -n AO-91 -h 24
```

### Get Passes
```bash
python -m amsatapi passes -o AO-91 -l CM85
```

## Downlod Telemetry Database Files
```bash
python -m amsatapi download-telemetry-database -n fox1d
```

## Download Telemetry Server Logs
```bash
python -m amsatapi download-telemetry-serverlogs -n fox1d
```

## Download TLE File (All AMSAT Published TLEs in one file)
```bash
python -m amsatapi tle > tle.txt
```

### Download TLE for Single Spacecraft by Name (Names from TLE File)
```bash
python -m amsatapi tle -n AO-91
```
