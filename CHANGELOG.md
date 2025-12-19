# Changelog

All notable changes to this project will be documented in this file.

## [v0.0.2] - 2025-12-20

### ✨ UI & UX
- **Chess Invites**: Now display the sender's name (e.g., "Invite from **Node123**").
- **Accept Button**: Updates dynamically to "Play vs [Name]".
- **Traceroute**: Fixed "flashing" list by optimizing redraws.

### ⚡ Stability
- **Threading**: Game Invites and Trace requests are now threaded, preventing the UI from hanging/freezing during network operations.

### 📚 Documentation
- Added "Experimental/Unofficial" warning.

## [v0.0.1] - 2025-12-20

### 🚀 New Features
- **Multiplayer Chess**: Fully playable Chess game over Meshtastic DMs.
    - JSON-based protocol.
    - UCI notation for low bandwidth.
    - Automatic board orientation.
    - Invite/Accept workflow.
- **Traceroute Tab**:
    - Distance-based sorting (Haversine formula).
    - Threaded trace requests (30s countdown).
    - Visual report of hops.
- **Map Tab**: Integrated map with node markers.
- **Status Bar**: Display Battery, Sats, Utilization (ChUtil), and Node info.

### 🐛 Fixes & Improvements
- **Performance**: Fixed UI flashing in Traceroute tab by implementing smart list updates.
- **Stability**: Network operations (Invites, Trace requests) are now threaded to prevent UI hangs.
- **Crash Fix**: Resolved `AttributeError` on node selection.
- **Build**: Added `build.sh` for generating standalone macOS executables via PyInstaller.

### 🛠 Technical
- Added VSCode automation (`launch.json`, `tasks.json`) for easier contribution.
- Standardized `requirements.txt`.
