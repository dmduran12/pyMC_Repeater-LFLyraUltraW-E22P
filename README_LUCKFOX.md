# Luckfox Lyra Ultra W - pyMC Repeater Setup Guide

This device has been configured to run the **pyMC Repeater** service using an **E22-900M30S (SX1262)** LoRa module on a custom HAT.

## Hardware Configuration

### Pin Mapping (Luckfox Lyra 24-Pin Header)
The following pin mapping is critical for correct operation. Note that the Linux GPIO numbers differ from physical pin numbers.

| Signal | Physical Pin | Luckfox GPIO |
|--------|--------------|--------------|
| **MISO** | 7            | (SPI0_MISO)  |
| **MOSI** | 6            | (SPI0_MOSI)  |
| **CLK**  | 8            | (SPI0_CLK)   |
| **CS**   | 10           | (SPI0_CS0)   |
| **Reset**| 9            | GPIO 9       |
| **Busy** | 11           | GPIO 11      |
| **IRQ**  | 13           | GPIO 5       |
| **TXEN** | 14           | GPIO 14      |
| **RXEN** | N/C          | -1           |

### Power Configuration
*   **Regulator Mode**: `LDO` (Required for stable operation on this board/module combo).
*   **TCXO**: `Enabled` at `1.6V` (Hardware request was 1.4V, but SX1262 minimum is 1.6V).
*   **TX Power**: Set to `18` dBm.
*   **LEDs**: The Green TX LED is tied directly to the `TXEN` line (GPIO 14). It cannot be dimmed via software without compromising the radio transmission signal.

## Software Architecture

### GPIO Handling
The standard `gpiozero` library is incompatible with the Luckfox device due to missing RPi hardware identifiers. A custom wrapper has been implemented:
*   **`pymc_core/hardware/gpio_wrapper.py`**: A lightweight wrapper around `python-periphery` that mimics the `gpiozero` API (`Button`, `DigitalOutputDevice`).
*   **`pymc_core/hardware/gpio_manager.py`**: Refactored to use the custom wrapper.

### SPI Driver
*   **Speed**: Reduced to `100kHz` to ensure signal integrity.
*   **Chip Select**: Uses standard Linux SPI driver handling (CS0).

## Configuration File (`config.yaml`)

Key settings for this environment:

```yaml
radio:
  frequency: 927875000
  spreading_factor: 9
  bandwidth: 62500
  coding_rate: 5
  preamble_length: 17
  tx_power: 18
  sync_word: 18 # Private Network (0x12)

sx1262:
  bus_id: 0
  cs_id: 0
  cs_pin: -1    # Use hardware CS
  reset_pin: 9
  busy_pin: 11
  irq_pin: 5
  txen_pin: 14
  rxen_pin: -1
  txled_pin: -1
  rxled_pin: -1
  use_dio3_tcxo: true
  dio3_tcxo_voltage: 1.6 # Lowest supported by SX1262
```

## Deployment & Maintenance

### Restarting the Service
The service runs as a background python process. To restart:

```bash
pkill -f repeater.main
cd /root/pyMC_Repeater
nohup python3 -m repeater.main > /root/repeater.log 2>&1 &
```

### Viewing Logs
```bash
tail -f /root/repeater.log
```

### Accessing Dashboard
The device binds to `0.0.0.0:8000`. Access locally via ADB port forwarding:
```bash
adb forward tcp:8000 tcp:8000
# Open http://localhost:8000 in browser
```
