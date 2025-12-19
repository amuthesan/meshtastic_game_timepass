import customtkinter
import tkintermapview
import mesh_interface
from chess_ui import ChessBoardFrame
import threading
import time
from datetime import datetime
from mesh_interface import MeshInterface

customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("blue")

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Meshtastic Desktop Node")
        self.geometry("1100x700")

        # Grid configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # Tabview expands

        # --- Data Interface ---
        self.mesh_interface = MeshInterface()

        # --- Top Bar ---
        self.top_bar = customtkinter.CTkFrame(self, height=60, corner_radius=0)
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        # Re-configure columns for more items
        self.top_bar.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6, 7), weight=1)

        # --- Connection Controls ---
        self.var_port = customtkinter.StringVar(value="Select Port")
        self.combo_ports = customtkinter.CTkComboBox(self.top_bar, variable=self.var_port, values=[], width=150)
        self.combo_ports.grid(row=0, column=0, padx=10, pady=10)

        self.btn_refresh = customtkinter.CTkButton(self.top_bar, text="⟳", width=30, command=self.refresh_ports)
        self.btn_refresh.grid(row=0, column=1, padx=(0, 10), pady=10)

        self.btn_connect = customtkinter.CTkButton(self.top_bar, text="Connect", width=80, command=self.toggle_connection, fg_color="green")
        self.btn_connect.grid(row=0, column=2, padx=(0, 10), pady=10)

        # Labels for Top Bar (Shifted columns)
        self.label_node_name = customtkinter.CTkLabel(self.top_bar, text="Node: --", font=("Roboto Medium", 16))
        self.label_node_name.grid(row=0, column=3, padx=10, pady=10)

        self.label_battery = customtkinter.CTkLabel(self.top_bar, text="Battery: --%", text_color="gray")
        self.label_battery.grid(row=0, column=4, padx=10, pady=10)

        self.label_time = customtkinter.CTkLabel(self.top_bar, text="Time: --:--")
        self.label_time.grid(row=0, column=5, padx=10, pady=10)

        self.label_sats = customtkinter.CTkLabel(self.top_bar, text="Sats: --")
        self.label_sats.grid(row=0, column=6, padx=10, pady=10)

        self.label_chutil = customtkinter.CTkLabel(self.top_bar, text="ChUtil: --%")
        self.label_chutil.grid(row=0, column=7, padx=10, pady=10)

        # --- Tab View ---
        self.tab_view = customtkinter.CTkTabview(self)
        self.tab_view.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        
        self.tab_view.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        
        self.tab_messages = self.tab_view.add("Messages")
        self.tab_nodes = self.tab_view.add("Nearby Nodes")
        self.tab_trace = self.tab_view.add("Traceroute")
        self.tab_channels_settings = self.tab_view.add("Channel Settings") 
        self.tab_map = self.tab_view.add("Map")
        self.tab_game = self.tab_view.add("Game") # New Tab

        # --- Game Tab ---
        self.tab_game.grid_columnconfigure(0, weight=1)
        self.tab_game.grid_rowconfigure(0, weight=1)
        self.chess_frame = ChessBoardFrame(self.tab_game, mesh_interface=self.mesh_interface)
        self.chess_frame.grid(row=0, column=0, pady=20)

        # --- Messages Tab (Chat Interface) ---
        self.tab_messages.grid_columnconfigure(1, weight=1) # Chat area expands
        self.tab_messages.grid_rowconfigure(0, weight=1)

        self.sidebar_ui_buttons = {} # key: type_id, val: widget
        
        # 1. Sidebar (Channels & DMs)
        self.chat_sidebar = customtkinter.CTkScrollableFrame(self.tab_messages, width=200, corner_radius=0)
        self.chat_sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        
        self.lbl_channels = customtkinter.CTkLabel(self.chat_sidebar, text="CHANNELS", font=("Roboto", 12, "bold"), text_color="gray", anchor="w")
        self.lbl_channels.pack(pady=(10, 5), padx=10, fill="x")
        self.channel_buttons_frame = customtkinter.CTkFrame(self.chat_sidebar, fg_color="transparent")
        self.channel_buttons_frame.pack(fill="x")
        
        self.lbl_dms = customtkinter.CTkLabel(self.chat_sidebar, text="DIRECT MESSAGES", font=("Roboto", 12, "bold"), text_color="gray", anchor="w")
        self.lbl_dms.pack(pady=(20, 5), padx=10, fill="x")
        self.dm_buttons_frame = customtkinter.CTkFrame(self.chat_sidebar, fg_color="transparent")
        self.dm_buttons_frame.pack(fill="x")

        # 2. Chat Area
        # 2. Chat Area (Mini Tabs)
        # Instead of a single textbox, we use a TabView to hold active chats
        self.chat_tabs = customtkinter.CTkTabview(self.tab_messages)
        self.chat_tabs.grid(row=0, column=1, sticky="nsew", padx=10, pady=(0, 10))
        
        # We need a dictionary to track created tabs { 'type_id': tab_object }
        # Or just rely on tab name. Tab name must be unique. 
        # Let's use names like "Channel: Primary" or "DM: User"
        self.active_chat_tabs = [] 

        self.chat_entry_frame = customtkinter.CTkFrame(self.tab_messages, fg_color="transparent")
        self.chat_entry_frame.grid(row=1, column=1, sticky="ew", padx=10, pady=10)
        self.chat_entry_frame.grid_columnconfigure(0, weight=1)
        
        self.entry_message = customtkinter.CTkEntry(self.chat_entry_frame, placeholder_text="Type a message...")
        self.entry_message.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.entry_message.bind("<Return>", self.send_message_event)
        
        self.btn_send = customtkinter.CTkButton(self.chat_entry_frame, text="Send", width=100, command=self.send_message_event)
        self.btn_send.grid(row=0, column=1)

        # --- Nearby Nodes Tab ---
        self.tab_nodes.grid_columnconfigure(0, weight=1)
        self.tab_nodes.grid_rowconfigure(0, weight=1)
        # Using a monospaced textbox for simple table representation for now, or could use individual frames
        self.nodes_list_frame = customtkinter.CTkScrollableFrame(self.tab_nodes)
        self.nodes_list_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.nodes_ui_elements = {} # To keep track of node rows

        self.setup_traceroute_tab() 
        
        # --- Channel Settings Tab ---
        self.tab_channels_settings.grid_columnconfigure(0, weight=1)
        self.tab_channels_settings.grid_rowconfigure(0, weight=1)
        self.channels_scroll_frame = customtkinter.CTkScrollableFrame(self.tab_channels_settings)
        self.channels_scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.btn_refresh_channels = customtkinter.CTkButton(self.tab_channels_settings, text="Refresh Channels", command=self.update_channel_settings_tab)
        self.btn_refresh_channels.grid(row=1, column=0, pady=5)
        self.channels_ui_elements = []

        # --- Map Tab ---
        self.tab_map.grid_columnconfigure(0, weight=1)
        self.tab_map.grid_rowconfigure(0, weight=1)
        
        self.tab_map.grid_rowconfigure(0, weight=1)
        
        self.map_widget = tkintermapview.TkinterMapView(self.tab_map, corner_radius=10, max_zoom=19)
        self.map_widget.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.map_widget.set_position(4.2105, 101.9758) # Malaysia
        self.map_widget.set_zoom(6) 
        
        # Map Zoom Sensitivity Fix (Monkey Patching / Re-binding)
        # TkinterMapView usually binds to <MouseWheel>, <Button-4>, <Button-5>
        # We can try to unbind and bind custom if needed, or just let it be.
        # User said "zooms way too much". 
        # Attempt to reduce zoom step if possible? 
        # The library source uses `self.canvas.bind("<MouseWheel>", self.mouse_wheel)`
        # We can wrap the event handler.
        def constrained_mouse_wheel(event):
            # Reduce delta or ignore every other event?
            # Windows/MacOS delta is different.
            # Just calling original method with modified delta?
            # Or assume the library zooms by 1 level per event.
            # If we want finer control, we might need to intercept.
            # Actually, just suppress some events? 
            # Let's try to unbind first to see if we can control it.
            # self.map_widget.canvas.unbind("<MouseWheel>")
            pass
            
        # Better approach: The user wants "finer control". 
        # Maybe the default zoom step is too big (1 level). 
        # TkinterMapView doesn't easily support fractional zoom on scroll usually.
        # But we can try to disable scroll zoom and add +/- buttons? 
        # Or just leave it. The user said "zooms way too much".
        # Let's try to set use_database_only=True ?? No.
        
        # NOTE: Simple fix might not be possible without library mod.
        # I will add Zoom In/Out buttons on map as alternative for "Finer Control" 
        # if wheel is too jumpy.
        
        self.map_zoom_frame = customtkinter.CTkFrame(self.tab_map, fg_color="transparent")
        self.map_zoom_frame.grid(row=0, column=0, sticky="se", padx=20, pady=20)
        
        self.btn_zoom_in = customtkinter.CTkButton(self.map_zoom_frame, text="+", width=30, command=lambda: self.map_widget.set_zoom(self.map_widget.zoom + 0.5))
        self.btn_zoom_in.pack(pady=5)
        self.btn_zoom_out = customtkinter.CTkButton(self.map_zoom_frame, text="-", width=30, command=lambda: self.map_widget.set_zoom(self.map_widget.zoom - 0.5))
        self.btn_zoom_out.pack(pady=5)
        
        self.map_markers = {}

        # Start Update Loop
        self.refresh_ports()
        self.update_gui_loop()

    def refresh_ports(self):
        ports = self.mesh_interface.get_available_ports()
        if not ports:
            ports = ["No Ports Found"]
        self.combo_ports.configure(values=ports)
        if ports and ports[0] != "No Ports Found":
            self.combo_ports.set(ports[0])
        else:
            self.combo_ports.set("Select Port")

    def toggle_connection(self):
        if self.mesh_interface.connected:
            # Disconnect
            self.mesh_interface.disconnect()
            self.btn_connect.configure(text="Connect", fg_color="green")
            self.label_node_name.configure(text="Node: --")
        else:
            # Connect
            port = self.var_port.get()
            if port and port != "Select Port" and port != "No Ports Found":
                self.btn_connect.configure(text="Connecting...", state="disabled")
                self.update_idletasks() # Force update UI
                
                # Run connection in a separate thread to avoid freezing UI? 
                # For now let's just do it directly; it's usually fast enough or we accept a small freeze.
                # Actually, blocking the main thread is bad if it hangs.
                # But simple connect shouldn't hang forever.
                success = self.mesh_interface.connect(port)
                
                self.btn_connect.configure(state="normal")
                if success:
                    self.btn_connect.configure(text="Disconnect", fg_color="red")
                else:
                    self.btn_connect.configure(text="Connect", fg_color="green")
                    # Could show error popup
            else:
                 print("Invalid port selected")

    def update_gui_loop(self):
        # Update Time
        now = datetime.now().strftime("%H:%M:%S")
        self.label_time.configure(text=f"Time: {now}")

        # Update Node Info
        my_info = self.mesh_interface.get_my_info()
        if my_info:
            user = my_info.get('user', {})
            long_name = user.get('longName', 'Unknown')
            self.label_node_name.configure(text=f"Node: {long_name}")
            
            # Update Telemetry from local node or my info
            # Usually 'my_info' from getMyNodeInfo() has user details.
            # Device metrics might be separate. 
            # We can try to use the new get_telemetry method with our own ID.
            if 'id' in user:
                metrics = self.mesh_interface.get_telemetry(user['id'])
                if metrics:
                    bat = metrics.get('batteryLevel')
                    ch_util = metrics.get('channelUtilization')
                    sats = metrics.get('sats')
                    
                    if bat is not None:
                         self.label_battery.configure(text=f"Battery: {bat}%")
                    if ch_util is not None:
                         self.label_chutil.configure(text=f"ChUtil: {ch_util:.1f}%")
                    if sats is not None:
                         self.label_sats.configure(text=f"Sats: {sats}")

        # Update Sidebar (Channels & DMs)
        self.update_sidebar()
        
        # Update current chat view (if active tab)
        self.update_chat_tabs()
        # self.update_chat_display() # New method uses tabs

        # Update Traceroute display if active
        self.update_trace_tab() # Split UI update


        # Update Nodes List & Map
        nodes = self.mesh_interface.get_nodes()
        self.update_nodes_tab(nodes)
        self.update_map_tab(nodes)

        # Schedule next update
        self.after(2000, self.update_gui_loop)

    def update_nodes_tab(self, nodes):
        # Clear existing? Or update intelligently. For simplicity, we can clear and redraw if list changes size, or just update values.
        # Let's just create rows if they don't exist.
        
        for node_id, node_data in nodes.items():
            user = node_data.get('user', {})
            short_name = user.get('shortName', node_id)
            long_name = user.get('longName', 'Unknown')
            snr = node_data.get('snr', 0)
            last_heard = node_data.get('lastHeard', 0)
            
            # Format last heard
            lh_str = "Never"
            if last_heard > 0:
                elapsed = int(time.time() - last_heard)
                lh_str = f"{elapsed}s ago"

            # Create or update row
            if node_id not in self.nodes_ui_elements:
                row_frame = customtkinter.CTkFrame(self.nodes_list_frame)
                row_frame.pack(fill="x", pady=5)
                
                lbl_name = customtkinter.CTkLabel(row_frame, text=f"{long_name} ({short_name})", width=200, anchor="w")
                lbl_name.pack(side="left", padx=10)
                
                lbl_snr = customtkinter.CTkLabel(row_frame, text=f"SNR: {snr:.2f}", width=100)
                lbl_snr.pack(side="left", padx=10)
                
                lbl_lh = customtkinter.CTkLabel(row_frame, text=f"Last Heard: {lh_str}", width=100)
                lbl_lh.pack(side="left", padx=10)
                
                self.nodes_ui_elements[node_id] = {
                    'frame': row_frame,
                    'lbl_name': lbl_name,
                    'lbl_snr': lbl_snr,
                    'lbl_lh': lbl_lh
                }
            else:
                # Update existing
                ui = self.nodes_ui_elements[node_id]
                ui['lbl_snr'].configure(text=f"SNR: {snr:.2f}")
                ui['lbl_lh'].configure(text=f"Last Heard: {lh_str}")

    def update_map_tab(self, nodes):
        for node_id, node_data in nodes.items():
            if 'position' in node_data:
                pos = node_data['position']
                lat = pos.get('latitude')
                lon = pos.get('longitude')
                
                if lat and lon and lat != 0 and lon != 0:
                    user = node_data.get('user', {})
                    name = user.get('shortName', node_id)
                    
                    if node_id not in self.map_markers:
                        # Use a simpler marker (circle) if possible.
                        # Using standard marker for now but user asked for "generated small pin".
                        # TkinterMapView supports custom images. 
                        # We can just use the default marker but maybe it's too big? 
                        # There isn't a built-in "small dot" in this lib without an image.
                        # I will assume standard marker is okay for now, or use a text-only marker?
                        # Let's try to pass 'text_color' or something? No.
                        # To truly fix "make pin smaller", we need an icon. 
                        # I will rely on default for now as I cannot easily generate a binary icon file here without `generate_image`.
                        # Actually, wait, I can use a small shape if supported? No.
                        marker = self.map_widget.set_marker(lat, lon, text=name)
                        self.map_markers[node_id] = marker
                    else:
                        marker = self.map_markers[node_id]
                        marker.set_position(lat, lon)

    def update_sidebar(self):
        # Optimized Sidebar Update
        # Instead of destroying all, we check what exists.
        
        # CHANNELS
        channels = self.mesh_interface.get_channels()
        current_channel_ids = {ch['index'] for ch in channels}
        
        # Remove old buttons
        to_remove = []
        for key in self.sidebar_ui_buttons:
            type, id = key.split('_')
            if type == 'channel' and int(id) not in current_channel_ids:
                to_remove.append(key)
        for key in to_remove:
            self.sidebar_ui_buttons[key].destroy()
            del self.sidebar_ui_buttons[key]
            
        # Add new buttons or update
        for ch in channels:
            idx = ch['index']
            name = ch['name']
            key = f"channel_{idx}"
            
            if key not in self.sidebar_ui_buttons:
                btn = customtkinter.CTkButton(self.channel_buttons_frame, text=f"# {name}", 
                                              fg_color="transparent", text_color=("gray10", "gray90"), anchor="w",
                                              command=lambda i=idx, n=name: self.open_chat_tab('channel', i, n))
                btn.pack(fill="x", padx=5, pady=2)
                self.sidebar_ui_buttons[key] = btn
            
            # Update visuals if selected (Actually logic moved to tabs, highlight active tab?)
            # Sidebar selection emphasis might be less relevant if using tabs, but good to keep.
            # We can highlight if open? 

        # DMS
        nodes = self.mesh_interface.get_nodes()
        dm_ids = set(self.mesh_interface.chats['dms'].keys())
        # Also include nodes that we just know about? User requested "Direct Messages list"
        # Usually only active chats or favorites.
        # But for now, let's list active chats + known nodes.
        # Merging lists.
        all_ids = dm_ids.union(set(nodes.keys()))
        
        # Remove old
        to_remove = []
        for key in self.sidebar_ui_buttons:
            type, id_str = key.split('_', 1) # split only once
            if type == 'dm':
                try:
                    nid = int(id_str) # ID is int
                except:
                    nid = id_str # ID is string
                if nid not in all_ids:
                    to_remove.append(key)
        for key in to_remove:
            self.sidebar_ui_buttons[key].destroy()
            del self.sidebar_ui_buttons[key]
            
        # Add new
        for nid in all_ids:
            name = nid
            if nid in nodes:
                name = nodes[nid].get('user', {}).get('longName', nid)
            
            key = f"dm_{nid}"
            if key not in self.sidebar_ui_buttons:
                btn = customtkinter.CTkButton(self.dm_buttons_frame, text=f"@ {name}", 
                                              fg_color="transparent", text_color=("gray10", "gray90"), anchor="w",
                                              command=lambda i=nid, n=name: self.open_chat_tab('dm', i, n))
                btn.pack(fill="x", padx=5, pady=2)
                self.sidebar_ui_buttons[key] = btn

    def open_chat_tab(self, type, id, name):
        # Open a "Mini Tab" for this chat
        tab_name = f"{'#' if type=='channel' else '@'}{name}"
        
        # Check if tab exists
        try:
            self.chat_tabs.get(tab_name)
        except ValueError:
            # Create it
            self.chat_tabs.add(tab_name)
            # Add Textbox inside
            txt = customtkinter.CTkTextbox(self.chat_tabs.tab(tab_name), state="disabled")
            txt.pack(expand=True, fill="both", padx=5, pady=5)
            self.active_chat_tabs.append({'name': tab_name, 'type': type, 'id': id, 'widget': txt})
            
        # Switch to it
        self.chat_tabs.set(tab_name)
        self.current_chat_target = {'type': type, 'id': id, 'name': name}
        
        # Immediately populate
        self.update_chat_tabs(force_scroll=True)

    def update_chat_tabs(self, force_scroll=False):
        # Update ALL open tabs
        for tab_info in self.active_chat_tabs:
            type = tab_info['type']
            id = tab_info['id']
            widget = tab_info['widget']
            
            # Get messages
            msgs = []
            if type == 'channel':
                msgs = self.mesh_interface.chats['channels'].get(id, [])
            else:
                msgs = self.mesh_interface.chats['dms'].get(id, [])
                
            # Render (simple full redraw for now)
            # Optimization: check if count changed
            
            widget.configure(state="normal")
            widget.delete("1.0", "end")
            
            for m in msgs:
                 sender_name = m['from']
                 nodes = self.mesh_interface.get_nodes()
                 if m['is_self']:
                     sender_name = "Me"
                 elif m['from'] in nodes:
                     sender_name = nodes[m['from']].get('user', {}).get('shortName', m['from'])
                 
                 t_str = datetime.fromtimestamp(m['time']).strftime("%H:%M")
                 widget.insert("end", f"[{t_str}] {sender_name}: {m['text']}\n")
                 
            widget.configure(state="disabled")
            if force_scroll:
                 widget.see("end")

    def select_chat(self, type, id, name):
        # Deprecated legacy redirect
        self.open_chat_tab(type, id, name)


    def setup_traceroute_tab(self):
        # Configure Grid
        self.tab_trace.grid_columnconfigure(0, weight=1) # List
        self.tab_trace.grid_columnconfigure(1, weight=2) # Report
        self.tab_trace.grid_rowconfigure(0, weight=1)
        
        # --- Left Pane: Node List ---
        self.frame_trace_left = customtkinter.CTkFrame(self.tab_trace)
        self.frame_trace_left.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        customtkinter.CTkLabel(self.frame_trace_left, text="Nodes (Near -> Far)", font=("Roboto", 14, "bold")).pack(pady=5)
        
        self.trace_nodes_frame = customtkinter.CTkScrollableFrame(self.frame_trace_left)
        self.trace_nodes_frame.pack(expand=True, fill="both", padx=5, pady=5)
        
        # --- Right Pane: Controls & Report ---
        self.frame_trace_right = customtkinter.CTkFrame(self.tab_trace)
        self.frame_trace_right.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # Top Config (Persistent)
        self.frame_trace_config = customtkinter.CTkFrame(self.frame_trace_right, fg_color="transparent")
        self.frame_trace_config.pack(fill="x", padx=5, pady=5)
        
        customtkinter.CTkLabel(self.frame_trace_config, text="Destination ID/Name:").pack(side="left", padx=5)
        self.entry_trace_dest = customtkinter.CTkEntry(self.frame_trace_config, width=150)
        self.entry_trace_dest.pack(side="left", padx=5)
        
        self.btn_start_trace = customtkinter.CTkButton(self.frame_trace_config, text="Start Trace to Selected", 
                                                       command=self.start_trace_selected)
        self.btn_start_trace.pack(side="left", padx=5)
        
        # Status Label
        self.lbl_trace_status = customtkinter.CTkLabel(self.frame_trace_right, text="Select a node...", font=("Roboto", 12))
        self.lbl_trace_status.pack(pady=5)
        
        # Report Area
        self.trace_display = customtkinter.CTkTextbox(self.frame_trace_right, state="disabled")
        self.trace_display.pack(expand=True, fill="both", padx=5, pady=5)
        
        self.trace_selected_node = None

    def update_trace_tab(self):
        # 1. Update Node List (Left)
        nodes = self.mesh_interface.get_nodes()
        node_list = []
        
        # Get my position for distance calc
        my_lat = None
        my_lon = None
        if self.mesh_interface.interface and hasattr(self.mesh_interface.interface, 'localNode'):
             p = getattr(self.mesh_interface.interface.localNode, 'position', {})
             if 'latitude' in p and 'longitude' in p:
                  my_lat = p['latitude']
                  my_lon = p['longitude']
        
        for nid, data in nodes.items():
            user = data.get('user', {})
            short_name = user.get('shortName', str(nid))
            long_name = user.get('longName', f"Node {nid}")
            snr = data.get('snr', -100)
            
            # Calculate Distance
            dist = 999999999
            dist_str = ""
            if my_lat and 'position' in data:
                 pos = data['position']
                 if 'latitude' in pos and 'longitude' in pos:
                      d_m = self.mesh_interface.haversine(my_lat, my_lon, pos['latitude'], pos['longitude'])
                      dist = d_m
                      dist_str = f"{d_m/1000:.1f}km"
            
            node_list.append({'id': nid, 'name': short_name, 'long': long_name, 'snr': snr, 'dist': dist, 'dist_str': dist_str})
            
        # Sort by Distance ASC, then SNR DESC
        node_list.sort(key=lambda x: (x['dist'], -x['snr']))
        
        # Check if list changed (Simple hash of IDs and SNRs/Dist)
        # Or faster: just IDs? No, SNR updates matter?
        # User said "make it static, we dont have to keep refreshing".
        # Let's only update if the LIST OF IDs changes, or if manually requested?
        # Compromise: Check if the set of IDs and their order is identical.
        current_signature = [(n['id'], n['dist_str'], n['snr']) for n in node_list]
        
        if not hasattr(self, '_last_trace_node_sig') or self._last_trace_node_sig != current_signature:
             self._last_trace_node_sig = current_signature
             
             # Re-draw list
             for widget in self.trace_nodes_frame.winfo_children():
                 widget.destroy()
                 
             for n in node_list:
                 info = f"{n['long']}"
                 if n['dist_str']:
                      info += f" ({n['dist_str']})"
                 else:
                      info += f" (SNR: {n['snr']})"
                      
                 btn = customtkinter.CTkButton(self.trace_nodes_frame, text=info, 
                                               command=lambda nid=n['id']: self.select_trace_node(nid))
                 btn.pack(fill="x", pady=2)
            
        # 2. Update Report (Right)
        if self.trace_selected_node:
             # Check for results
             traces = self.mesh_interface.get_trace(self.trace_selected_node)
             
             # Only update text if content differs to avoid flickering cursor?
             # Textbox doesn't flicker as much as cleared frames.
             # But let's check content.
             new_text = f"Route to {self.trace_selected_node}:\n"
             if traces:
                 for i, hop in enumerate(traces):
                      new_text += f"  Hop {i+1}: {hop}\n"
             else:
                  new_text += "  Waiting for trace..."
             
             # Current text?
             # reading textbox is expensive?
             # Just set it? Textbox usually handles update ok.
             # But if user selects text it resets.
             # Let's simple-update for now.
             
             if traces:
                 self.trace_display.configure(state="normal")
                 current_content = self.trace_display.get("1.0", "end").strip()
                 if current_content != new_text.strip():
                      self.trace_display.delete("1.0", "end")
                      self.trace_display.insert("end", new_text)
                 self.trace_display.configure(state="disabled")

    def select_trace_node(self, nid):
        self.trace_selected_node = nid
        
        # UI Feedback: Update Entry and Label
        # Find name if possible
        nodes = self.mesh_interface.get_nodes()
        name = str(nid)
        if nid in nodes:
             name = nodes[nid].get('user', {}).get('shortName', str(nid))
             
        self.entry_trace_dest.delete(0, "end")
        self.entry_trace_dest.insert(0, name) # Or ID if preferred, but name is friendlier
        
        self.lbl_trace_status.configure(text=f"Target: {name}")
        
        self.update_trace_tab()

    def start_trace_selected(self):
        if self.trace_selected_node:
             # Thread the sending to prevent UI freeze
             threading.Thread(target=self.mesh_interface.send_trace_route, args=(self.trace_selected_node,)).start()
             
             # UI Feedback & Countdown
             self.btn_start_trace.configure(state="disabled", text="Tracing... (30s)")
             self.trace_display.configure(state="normal")
             self.trace_display.insert("end", f"\n[{datetime.now().strftime('%H:%M:%S')}] Request Sent to {self.trace_selected_node}...\n")
             self.trace_display.configure(state="disabled")
             self.trace_display.see("end")
             
             # Start Countdown
             self.trace_countdown(30)

    def trace_countdown(self, seconds_left):
        if seconds_left > 0:
            self.btn_start_trace.configure(text=f"Tracing... ({seconds_left}s)")
            # Check if we got a response meanwhile? 
            # If we did, we could stop early, but multiple hops come in. 
            # Let's run full duration or until user cancels (no cancel yet).
            
            # Non-blocking wait
            self.after(1000, lambda: self.trace_countdown(seconds_left - 1))
        else:
            self.btn_start_trace.configure(state="normal", text="Start Trace to Selected")
            self.trace_display.configure(state="normal")
            self.trace_display.insert("end", f"Trace window ended.\n")
            self.trace_display.configure(state="disabled")
            self.trace_display.see("end")

    def send_message_event(self, event=None):
        text = self.entry_message.get()
        if text:
            target = self.current_chat_target
            if target['type'] == 'channel':
                self.mesh_interface.send_message(text, channelIndex=target['id'])
            else:
                self.mesh_interface.send_message(text, destinationId=target['id'])
                
            self.entry_message.delete(0, "end")
            self.update_chat_display(force_scroll=True)

    def start_trace_event(self):
        target = self.entry_trace_dest.get()
        if not target:
            return
            
        # If user entered a name, try to resolve to ID
        nodes = self.mesh_interface.get_nodes()
        target_id = None
        
        # Try as int
        try:
            target_id = int(target) # e.g. !1234
        except:
             # Try as name
             for nid, data in nodes.items():
                 user = data.get('user', {})
                 if user.get('longName') == target or user.get('shortName') == target:
                     target_id = nid
                     break
        
        # If still not found, assumes it might be ID string like '!1234' which python can't int() directly
        # Actually meshtastic uses numeric IDs internally mostly but '!' notation is common string rep.
        # Let's just pass whatever we found or string.
        # If target_id is None, maybe use target string directly if it starts with '!'?
        
        if not target_id:
            # Simple check if looks like ID
            if target.startswith('!'):
                 # Convert hex to int? Or just assume it's lost and pass as is?
                 # Assuming meshtastic serial interface might handle it?
                 target_id = target # Interface usually expects Number.
                 # Let's warn if not resolved.
            else:
                # Could be a raw number entered as string
                try:
                    target_id = int(target)
                except:
                     pass

        if target_id:
            self.trace_display.configure(state="normal")
            self.trace_display.insert("end", f"Sending trace to {target} ({target_id})...\n")
            self.trace_display.configure(state="disabled")
            self.mesh_interface.send_trace_route(target_id)
            # Should start monitoring result? Result comes in callback on_meshtastic_message
            # We can poll get_trace() in update loop?
            # Or just update display periodically.
            # Ideally we have a 'trace_in_progress' state.
        else:
             print("Could not resolve node for trace")

    def update_channel_settings_tab(self):
        # Re-build list only if changes? Or just clear/redraw (inefficient but safe)
        for widget in self.channels_scroll_frame.winfo_children():
            widget.destroy()
            
        channels = self.mesh_interface.get_channels()
        for ch in channels:
            frame = customtkinter.CTkFrame(self.channels_scroll_frame)
            frame.pack(fill="x", pady=5, padx=5)
            
            lbl_idx = customtkinter.CTkLabel(frame, text=f"{ch['index']}", font=("Roboto", 14, "bold"), width=30)
            lbl_idx.pack(side="left", padx=10)
            
            lbl_name = customtkinter.CTkLabel(frame, text=f"Name: {ch['name']}", width=120, anchor="w")
            lbl_name.pack(side="left", padx=10)
            
            lbl_role = customtkinter.CTkLabel(frame, text=f"Role: {ch['role']}", width=100)
            lbl_role.pack(side="left", padx=10)
            
            lbl_psk = customtkinter.CTkLabel(frame, text=f"PSK: {ch.get('psk', 'None')}", width=100, text_color="gray")
            lbl_psk.pack(side="left", padx=10)
            
            # Uplink/Downlink indicators
            ul = "UL: " + ("ON" if ch.get('uplink') else "OFF")
            dl = "DL: " + ("ON" if ch.get('downlink') else "OFF")
            lbl_opts = customtkinter.CTkLabel(frame, text=f"{ul}  {dl}", width=120)
            lbl_opts.pack(side="left", padx=10)

    def update_trace_display(self):
        # Check if we have any traces to show for the LAST target?
        # Ideally we track the last requested target ID or list all?
        # For simplicity, let's just check if there's any updates or show all.
        # But our display is a simple textbox. 
        # Let's see if we have a target active target from the text entry?
        # Or better, just dump the latest trace received.
        
        # Let's iterate over self.mesh_interface.traces
        traces = self.mesh_interface.traces
        if not traces:
            return
            
        current_text = self.trace_display.get("1.0", "end")
        
        # Simple approach: If new trace data differs from what we displayed, append/update?
        # A full log style might be better.
        # Let's just append new checks.
        
        # For this PoC, I will just re-print everything if it changes, or just append "Received trace from X: ..."
        # since we print to console in backend.
        
        # Let's make it pull from backend's last_trace maybe?
        # Or just read the dict.
        
        # To avoid spamming, we only update if content changed? 
        # Hard to track state of textbox vs dict.
        
        # Improved logic: Clear and Redraw fully (simple)
        self.trace_display.configure(state="normal")
        self.trace_display.delete("1.0", "end")
        for sender, route in traces.items():
            self.trace_display.insert("end", f"Trace from {sender}:\n")
            for i, hop in enumerate(route):
                self.trace_display.insert("end", f"  Hop {i+1}: {hop}\n")
            self.trace_display.insert("end", "-"*20 + "\n")
        self.trace_display.configure(state="disabled")




    def on_closing(self):
        self.mesh_interface.close()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
