# homeassistant-pypowerwall

Custom Home Assistant integration for Tesla Powerwall 3 systems. This might work for Powerwall 2 and Powerwall+ systems too, as this really is just a front-end for [pypowerwall](https://github.com/jasonacox/pypowerwall).

Mostly this is a quick integration made in anger. Hopefully it works for others and saves some headache.


## Exposed Entities

**15 entities**:

| Entity | Unit | Notes |
|---|---|---|
| Grid Power | W | Positive = importing from grid |
| Solar Power | W | |
| Battery Power | W | Positive = charging |
| Home Consumption | W | |
| Grid Energy Imported | kWh | Lifetime cumulative |
| Grid Energy Exported | kWh | Lifetime cumulative |
| Solar Energy Generated | kWh | Lifetime cumulative |
| Battery Energy Charged | kWh | Lifetime cumulative |
| Battery Energy Discharged | kWh | Lifetime cumulative |
| Home Energy Consumed | kWh | Lifetime cumulative |
| Battery Level | % | |
| Grid Status | — | Up / Down / Syncing |
| Backup Time Remaining | h | |
| Battery Reserve | % | Configured backup reserve |
| Battery Mode | — | self_consumption / backup / autonomous |


## Installation

1. Copy `custom_components/pypowerwall/` into `/config/custom_components/pypowerwall/` on your Home Assistant instance.
2. Restart Home Assistant.
3. Go to **Settings → Integrations → Add Integration** and search for **pypowerwall**.
4. Enter your gateway IP and password (see 'Network Connection' below).


## Network connection

You need to connect to the Powerwall 3 unit's Access Point directly - notably not the Gateway unit. They are separate devices with separate credentials. Annoyingly, Tesla has seen fit to hide these credentials **inside** the Powerwall, so the first step is that you need to unscrew the front panel to get it (or ask your electrician as they're installing the damned thing). You should find a sticker with an SSID and WiFi password quite obviously once you do this. Save this password somewhere else if you can.

pypowerwall connects to the Tesla Gateway's TEDAPI endpoint at `192.168.91.1`. This address is only reachable via the Gateway's own Wi-Fi access point, so your Home Assistant host must be able to reach `192.168.91.1` in addition to your home network.

### If your HA host can connect to the Gateway's Wi-Fi directly

This is the easy situation. If you have your box just connected via ethernet and you have a spare WiFi receiver on it not doing anything, then just connect to the 

### If your HA host is too far from the Gateway to connect to its Wi-Fi

Then this might turn into a mini-project to get running. You need to setup a small bridge device near the Gateway. something with both a Wi-Fi radio (to connect to the Gateway) and an Ethernet port (to connect back to your home network) would be ideal. You'll then need to setup a static route in Home Assistant. Do your own research here, as there'll be gotchas.
