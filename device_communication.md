# Rinnai Water Heater Local Communication Protocol

This document provides a technical specification of the local network communication protocol used by Rinnai Wi-Fi Water Heaters (such as model **REUE271FEHGN3** and compatible series). 

The device communicates via unencrypted **HTTP REST endpoints** on port 80 and listens for **UDP Broadcasts** on port 8080 for IP discovery.

---

## 1. Protocol Architecture & Connection Flow

When the official application opens or an integration initializes, it interacts with the water heater using the following flow:

```
[ Client / Home Assistant ]
         │
         ├──► GET /connect          ──► Returns MAC Address
         ├──► GET /read_modelo      ──► Returns Hardware Model
         ├──► GET /bus              ──► Returns Complete Real-Time Telemetry (CSV)
         │
         ├──► GET /lig              ──► Toggles Power (On/Off)
         ├──► GET /inc              ──► Increments Target Temp (+1°C)
         └──► GET /dec              ──► Decrements Target Temp (-1°C)
```

---

## 2. HTTP Endpoints Summary

| Endpoint | HTTP Method | Description | Response Format |
| :--- | :---: | :--- | :--- |
| `/connect` | `GET` | Retrieve device MAC address | Plain text string (e.g. `3c:e9:0e:e1:75:58`) |
| `/read_modelo` | `GET` | Retrieve device model identifier | Plain text string (e.g. `REUE271FEHGN3`) |
| `/bus` | `GET` | Primary status & telemetry endpoint | Comma-separated values (CSV) string |
| `/lig` | `GET` | Toggle device power state (On/Off) | Comma-separated values (CSV) screen status |
| `/inc` | `GET` | Increase target temperature by 1°C | Comma-separated values (CSV) screen status |
| `/dec` | `GET` | Decrease target temperature by 1°C | Comma-separated values (CSV) screen status |
| `/pre_heat_set_date_time/{mm}/{hh}/1` | `GET` | Set time (unsupported/unresponsive on some firmware) | HTTP 200 / Empty |
| `/hardware` | `GET` | Hardware diagnostic info (unresponsive on some models) | HTTP 200 / Empty |

---

## 3. `/bus` Telemetry Payload Specification

The `/bus` endpoint returns a single line of comma-separated values (CSV) representing the complete operational state of the water heater.

### Sample Payloads

**Heater Off (Standby / Powered Down):**
```csv
41,0,0,4700,135,19188,10000,0,0,0,1837,2856,0,265,195,3800,192.168.0.177,null,6,23481142,52838,0,Aug 26 2024,15,Software/System restart,3c:e9:0e:e1:75:58,0,0,1684,0,1,0,0,559,926,0,0,-62,[0],2
```

**Heater On & Actively Heating (Burner Active):**
```csv
42,0,1,4700,135,19206,10000,3174,2163,17830,1565,3154,750,246,176,3800,192.168.0.177,null:pri,6,23481142,113619,0,Aug 26 2024,15,Software/System restart,3c:e9:0e:e1:75:58,0,0,1684,0,1,0,0,559,926,0,0,-54,[0],2
```

### Field-by-Field Schema

| Index | Field Name | Data Type | Scaling / Conversion | Unit | Description |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **0** | `status_code` | `int` | Exact value | - | Device operational status (`11`: Off, `41`: Standby, `42`: Heating). |
| **1** | `reserved_1` | `int` | - | - | Unknown/Reserved field (usually `0`). |
| **2** | `combustion_active` | `bool` | `1` = True, `0` = False | - | Indicates active gas burner combustion. |
| **3** | `number_of_activations` | `int` | Exact value | count | Total lifetime burner activation count. |
| **4** | `combustion_hours` | `int` | Exact value | hours | Total active burner operating hours. |
| **5** | `standby_hours` | `int` | Exact value | hours | Total powered standby operating hours. |
| **6** | `fan_self_diagnostic` | `int` | Value / 10 | Hz | Fan self-diagnostic metric. |
| **7** | `fan_rotation_hz` | `int` | Value / 10 | Hz | Live fan rotational frequency. |
| **8** | `pov_current_ma` | `int` | Value / 10 | mA | Proportional valve (POV) current. |
| **9** | `power_kcal_min` | `int` | Value / 100 | kcal/min | Calculated heating output power. |
| **10** | `inlet_temp` | `int` | Value / 100 | °C | Cold water inlet temperature (e.g. `1565` -> `15.65°C`). |
| **11** | `outlet_temp` | `int` | Value / 100 | °C | Hot water outlet temperature (e.g. `3154` -> `31.54°C`). |
| **12** | `actual_flow` | `int` | Value / 100 | L/min | Live water flow rate (e.g. `750` -> `7.50 L/min`). |
| **13** | `min_flow_activation` | `int` | Value / 100 | L/min | Minimum water flow threshold required to trigger burner. |
| **14** | `min_flow_deactivation` | `int` | Value / 100 | L/min | Minimum water flow threshold to maintain burner activation. |
| **15** | `target_temp` | `int` | Value / 100 | °C | Configured target temperature (e.g. `3800` -> `38.00°C`). |
| **16** | `device_ip` | `string` | Exact text | IPv4 | Local IPv4 address assigned to the Wi-Fi module. |
| **17** | `connection_mode` | `string` | Text | - | Cloud connection state (`null` or `null:pri`). |
| **18-21**| `internal_counters` | `int` | - | - | Internal firmware metrics / telemetry timestamps. |
| **22** | `firmware_build_date` | `string` | Exact text | - | Firmware build date string (e.g. `Aug 26 2024`). |
| **23-24**| `system_reset_reason`| `string` | Text | - | System restart classification (e.g. `Software/System restart`). |
| **25** | `mac_address` | `string` | Text | MAC | Device Wi-Fi MAC address (e.g. `3c:e9:0e:e1:75:58`). |
| **26-36**| `reserved_2` | `mixed` | - | - | Reserved diagnostics & hardware indicators. |
| **37** | `wifi_signal` | `int` | Exact value | dBm | Wi-Fi RSSI signal strength (e.g. `-54` dBm). |
| **38+** | `additional_fields` | `mixed` | - | - | Additional firmware telemetry flags. |

---

## 4. Control Endpoints & Screen Payload (`/tela_`)

Executing control actions (`/lig`, `/inc`, `/dec`) returns a reduced screen payload matching the structure of `/tela_`.

### Sample Control Response
```csv
41,0,0,135,19188,0,null,6,52839,Aug 26 2024,15,0,0,0
```

### Screen Payload Schema

| Index | Field Name | Data Type | Description |
| :---: | :--- | :---: | :--- |
| **0** | `status_code` | `int` | Status code (`11`, `41`, or `42`). |
| **1** | `reserved` | `int` | Reserved (always `0`). |
| **2** | `combustion_active` | `bool` | `1` = Combustion active, `0` = Inactive. |
| **3** | `combustion_hours` | `int` | Total combustion hours. |
| **4** | `standby_hours` | `int` | Total standby hours. |
| **5** | `actual_flow` | `int` | Live water flow (L/min). |
| **6** | `connection_mode` | `string` | Connection status string (`null` or `null:pri`). |
| **7** | `raw_target_temp` | `int` | Encoded target temperature (see mapping table below). |
| **8** | `invite_counter_token` | `int` | Internal counter; **last 3 digits match the second half of the 6-digit Invite Code**. |
| **9** | `firmware_date` | `string` | Firmware release date. |

---

## 5. Device Status Codes

| Code | Status | Description |
| :---: | :--- | :--- |
| **11** | `OFF` | Device is completely powered off (display off). |
| **41** | `STANDBY` | Device is powered ON, waiting for water flow (burner off). |
| **42** | `HEATING` | Device is powered ON and actively burning gas to heat flowing water. |

---

## 6. Raw Target Temperature Mapping Table

Control endpoints return target temperatures encoded as raw integer values (position 7 in the `/tela_` payload). The table below maps raw integer values to degrees Celsius (°C):

| Raw Value | Temperature (°C) | Raw Value | Temperature (°C) |
| :---: | :---: | :---: | :---: |
| **3** | 35.0 °C | **12** | 44.0 °C |
| **4** | 36.0 °C | **13** | 45.0 °C |
| **5** | 37.0 °C | **14** | 46.0 °C |
| **6** | 38.0 °C | **15** | 47.0 °C |
| **7** | 39.0 °C | **16** | 48.0 °C |
| **8** | 40.0 °C | **18** | 50.0 °C |
| **9** | 41.0 °C | **19** | 55.0 °C |
| **10** | 42.0 °C | **20** | 60.0 °C |
| **11** | 43.0 °C | | |

---

## 7. Invite Code Pairing Algorithm

The 6-digit Invite Code (e.g. `177839`) used in the mobile app and integration config flow is structured into two 3-digit segments `XXX YYY`:

1. **First 3 Digits (`XXX`)**: Represents the last octet of the water heater's IPv4 address.
   - Example: Code `177839` -> `XXX = 177` -> Device IP is `192.168.0.177` (matching local subnet).
2. **Last 3 Digits (`YYY`)**: Represents the trailing 3 digits of position 9 in the `/tela_` payload response (`52839` -> `839`).

---

## 8. Dynamic IP Discovery (UDP Broadcast)

If the water heater's IP address changes due to DHCP reassignment, the device can be discovered dynamically on the local network via UDP broadcast:

- **Protocol**: UDP Broadcast
- **Destination Address**: `255.255.255.255` (Broadcast)
- **Destination Port**: `8080`
- **Payload**: `IP` (2-byte ASCII string `0x49 0x50`)

Responding Rinnai water heater devices will reply over UDP back to the sender, revealing their current IPv4 address.
