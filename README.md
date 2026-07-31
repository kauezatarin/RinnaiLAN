# Rinnai Water Heater Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/kauezatarin/RinnaiLAN?color=blue)](https://github.com/kauezatarin/RinnaiLAN/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Home Assistant custom integration for controlling and monitoring **Rinnai Wi-Fi Water Heaters** over the local local network (LAN) without any cloud dependency.

<details>
<summary><b>Table of Contents</b></summary>

- [Features](#features)
- [Supported Devices](#supported-devices)
- [Installation](#installation)
  - [Option 1: HACS (Recommended)](#option-1-hacs-recommended)
  - [Option 2: Manual Installation](#option-2-manual-installation)
- [Configuration](#configuration)
- [Entities & Sensors](#entities--sensors)
- [Troubleshooting & Support](#troubleshooting--support)
  - [Recommended Network Setup](#recommended-network-setup)
  - [Enabling Debug Logging](#enabling-debug-logging)
  - [Submitting Issues](#submitting-issues)
- [License](#license)

</details>

---

## Features

- **100% Local Control (LAN)**: Works completely offline within your local network — fast response times and no cloud server outages.
- **No Firmware Modification**: Works out-of-the-box with the original Rinnai Wi-Fi module.
- **Water Heater Control**: Turn device on/off and set target temperature (35°C – 60°C).
- **Comprehensive Monitoring**: Real-time telemetry including water temperatures, actual flow rate, combustion status, operating hours, and Wi-Fi signal.
- **Easy UI Configuration**: Setup directly via Home Assistant UI using your heater's IP address or a 6-digit Invite Code.
- **Optimized Polling**: Instant feedback on user control actions with background updates.

---

## Supported Devices

- Tested with Rinnai Wifi Module ROU0031.

---

## Installation

### Option 1: HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=kauezatarin&repository=RinnaiLAN&category=integration)

1. Ensure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance.
2. In HACS, go to **Integrations** > click the **3 dots** (top right) > **Custom repositories**.
3. Add `https://github.com/kauezatarin/RinnaiLAN` as an **Integration** repository.
4. Search for **Rinnai Lan** and click **Download**.
5. Restart Home Assistant.

### Option 2: Manual Installation

1. Download the `rinnai` folder from the [latest release](https://github.com/kauezatarin/RinnaiLAN/releases).
2. Copy the `rinnai` directory into your Home Assistant `<config_dir>/custom_components/` folder:
   ```
   config/
   └── custom_components/
       └── rinnai/
           ├── __init__.py
           ├── api.py
           ├── config_flow.py
           ├── manifest.json
           └── ...
   ```
3. Restart Home Assistant.

---

## Configuration

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=rinnai)

1. In Home Assistant, go to **Settings** > **Devices & Services**.
2. Click **Add Integration** (bottom right).
3. Search for **Rinnai Water Heater Integration**.
4. Choose your preferred configuration method:
   - **Invite Code**: Enter the 6-digit invite code provided by your device/app.
   - **Manual IP**: Enter the IP address of your Rinnai water heater on your local network (e.g., `192.168.0.177`).

---

## Entities & Sensors

The integration automatically creates 8 entities under a single device in Home Assistant:

| Entity Name | Domain / Type | Unit | Description |
| :--- | :--- | :---: | :--- |
| **Rinnai Water Heater** | `water_heater` | °C | Main climate entity to power on/off and adjust target temperature (35°C to 60°C). |
| **Inlet Water Temperature** | `sensor` | °C | Current temperature of incoming cold water. |
| **Outlet Water Temperature** | `sensor` | °C | Current temperature of outgoing heated water. |
| **Actual Water Flow** | `sensor` | L/min | Live water flow rate through the heater. |
| **Combustion Active** | `binary_sensor` | - | `ON` when gas burner is actively heating water (`heat` device class). |
| **Number of Activations** | `sensor` | activations | Total counter of burner activation cycles. |
| **Combustion Hours** | `sensor` | h | Cumulative active combustion operating hours. |
| **Standby Hours** | `sensor` | h | Cumulative power standby hours. |
| **Wi-Fi Signal** | `sensor` | dBm | Wi-Fi RSSI signal strength of the heater. |

---

## Troubleshooting & Support

### Recommended Network Setup
- **Static IP**: Assign a DHCP reservation / static IP address to your Rinnai Wi-Fi module in your router settings to prevent IP address changes upon reboot.
- **Local Subnet**: Ensure your Home Assistant server and the Rinnai water heater reside on the same local subnet.

### Enabling Debug Logging

If you encounter issues, enable debug logging by adding the following snippet to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.rinnai: debug
```

After modifying `configuration.yaml`, restart Home Assistant and check the logs via **Settings** > **System** > **Logs**.

### Submitting Issues

Before opening a new issue on GitHub:
1. Check the [Open Issues](https://github.com/kauezatarin/RinnaiLAN/issues) to see if your problem has already been reported.
2. Enable debug logging and reproduce the issue.
3. Download integration diagnostics: **Settings** > **Devices & Services** > **Rinnai** > 3 dots > **Download diagnostics**.
4. Attach the sanitized debug logs and diagnostic file to your GitHub issue submission.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
