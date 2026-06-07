# ESP32-RSSI-Localization

A low-cost Indoor Positioning System (IPS) for real-time tracking using ESP32, RSSI signals, and trilateration.
<img width="1895" height="894" alt="image" src="https://github.com/user-attachments/assets/eb2433a0-6345-4ca0-9c54-1dcc4a246757" />
<img width="963" height="559" alt="image" src="https://github.com/user-attachments/assets/8e079579-a898-491d-8d15-6af850ed1ba5" />

## Overview
This project implements a complete Indoor Positioning System designed to track devices within a local environment. By analyzing the Received Signal Strength Indicator (RSSI) from multiple ESP32 beacons, the system estimates the user's coordinates using trilateration and visualizes the data on a live web dashboard.

## Key Features
* **Hybrid Scanning:** Simultaneous monitoring of WiFi and Bluetooth Low Energy (BLE) signals.
* **Low Latency:** Fast data transmission via UDP protocol for real-time updates.
* **Live Dashboard:** Interactive UI built with Streamlit and Matplotlib.
* **Flexible Configuration:** Dynamic adjustment of beacon coordinates and room dimensions directly from the sidebar.

The system converts signal strength into distance using the Log-Distance Path Loss Model:
$$d = 10^{\frac{A - RSSI}{10n}}$$

Where:
* $d$ – Estimated distance (m)
* $A$ – Reference signal strength at 1 meter (dBm)
* $RSSI$ – Current received signal strength indicator (dBm)
* $n$ – Path loss exponent (environment factor)

### Position Calculation
The final position $(x, y)$ is calculated via **trilateration**, solving the intersection of three circles centered at the respective beacon positions.

## System Architecture
1. **Beacons (ESP32):** Constantly scan/broadcast RSSI data and transmit packets via UDP.
2. **Bridge Script (`bridge.py`):** Acts as a local server collecting UDP data packets from the hardware layer.
3. **Dashboard (`dashboard.py`):** Processes distances, performs trilateration, and renders the web interface in real-time.



