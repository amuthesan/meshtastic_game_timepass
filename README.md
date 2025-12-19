# Meshtastic Desktop Node (with Multiplayer Chess)

A feature-rich Desktop GUI for [Meshtastic](https://meshtastic.org/) nodes, built with Python and CustomTkinter. 

This application connects to your Meshtastic device via USB/Serial and provides a user-friendly dashboard for messaging, mapping, network debugging, and **Multiplayer Gaming**.

## Features

### 📡 Core Mesh Functions
- **Serial Connection**: Auto-detects and connects to Meshtastic devices.
- **Messaging**: Integrated Chat and Direct Messages (DMs).
- **Node List**: Real-time list of peers with:
    - **Distance Sorting**: "Nearest to Farthest" (requires GPS).
    - **SNR**: Signal health monitoring.
- **Traceroute**:
    - dedicated tab for running trace routes.
    - Visual feedback and route reports.
    - Optimized list updates (no flashing).

### ♟️ Multiplayer Chess
Play Chess **over the mesh network**!
- **Zero-Setup**: Uses standard Direct Messages (DMs) to transmit moves.
- **Low Bandwidth**: Sends tiny JSON packets (e.g., `{"u": "e2e4"}`).
- **Interactive**:
    - Invite any node from the "Game" tab.
    - **Dynamic Orientation**: Board automatically flips if you are playing Black.
    - **Sound Effects**: Audio feedback for moves and captures.
    - **Guide Markers**: Highlights valid moves for beginners.

### 🗺️ Maps
- Offline-capable map view (TkinterMapView).
- Visualizes node positions.

## Installation

### Prerequisites
- Python 3.x
- A Meshtastic device connected via USB.

### Quick Start (Dev)
1.  Clone the repository:
    ```bash
    git clone https://github.com/amuthesan/meshtastic_game_timepass.git
    cd meshtastic_game_timepass
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the app:
    ```bash
    python main.py
    ```

### Building (Executable)
To create a standalone macOS application (`.app`):
```bash
./build.sh
```
Find the output in `dist/MeshtasticGUI.app`.

## Usage

### Playing Chess
1.  Connect your Meshtastic device.
2.  Go to the **Game** tab.
3.  Select a peer from the "Play against" dropdown (peers appear after discovery).
4.  Click **Invite**.
5.  Wait for them to accept.
    - **Host (Inviter)** plays White.
    - **Guest (Accepter)** plays Black.

## Contributing
1.  Open the folder in **VSCode**.
2.  The `.vscode` folder contains tasks to automatically install dependencies and run the debugger.
3.  Press **F5** to start.

## License
MIT
