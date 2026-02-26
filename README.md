ESP32-RSSI-Localization - A low-cost Indoor Positioning System (IPS) for real-time tracking
<img width="1895" height="894" alt="image" src="https://github.com/user-attachments/assets/eb2433a0-6345-4ca0-9c54-1dcc4a246757" />

This project implements a complete Indoor Positioning System designed to track devices within a local environment. By analyzing the Received Signal Strength Indicator (RSSI) from multiple ESP32 beacons, the system estimates the user's coordinates using trilateration and visualizes the data on a live web dashboard.

Key Features:
- Hybrid Scanning: Simultaneous monitoring of WiFi and Bluetooth Low Energy (BLE) signals.
- Low Latency: Data transmission via UDP protocol for real-time updates.
- Live Dashboard: Interactive UI built with Streamlit and Matplotlib.
- Flexible Configuration: Dynamic adjustment of beacon coordinates and room dimensions.

The system converts signal strength into distance using the Log-Distance Path Loss Model:
$$d = 10^{\frac{A - RSSI}{10n}}$$

$d$: Estimated distance (m)$A$: Reference signal strength at 1 meter (dBm)$RSSI$: Current signal strength (dBm)$n$: Path loss exponent (environment factor)The final position $(x, y)$ is calculated via trilateration, solving the intersection of three circles centered at beacon positions.
