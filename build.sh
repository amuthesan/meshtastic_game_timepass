#!/bin/bash
echo "Building MeshtasticGUI..."

# Ensure dependencies are installed
pip3 install -r requirements.txt

# Clean previous build
rm -rf build dist

# Find CustomTkinter path for data inclusion
CTK_PATH=$(python3 -c "import customtkinter; import os; print(os.path.dirname(customtkinter.__file__))")

# Build
echo "Using CustomTkinter at: $CTK_PATH"
pyinstaller --noconfirm --onefile --windowed --name "MeshtasticGUI" \
    --add-data "$CTK_PATH:customtkinter/" \
    --add-data "chess_ui.py:." \
    --add-data "chess_engine.py:." \
    --add-data "mesh_interface.py:." \
    --add-data "gui.py:." \
    main.py

echo "Build Complete! Executable is in dist/MeshtasticGUI.app"
