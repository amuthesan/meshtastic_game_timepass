import meshtastic.serial_interface
import meshtastic.protobuf.mesh_pb2
import serial.tools.list_ports
import threading
import time
import math
import json
from datetime import datetime
from pubsub import pub

class MeshInterface:
    def __init__(self):
        self.interface = None
        self.nodes = {}
        self.my_node_info = {}
        self.connected = False
        
        # Chat storage: 
        # 'channels': { index: [ {from, text, time}, ... ] }
        # 'dms': { node_id: [ {from, text, time}, ... ] }
        self.chats = {
            'channels': {},
            'dms': {}
        }
        self.traces = {} # dest_id: [hops...]
        
        # We start disconnected. User must select port.
        pub.subscribe(self.on_meshtastic_message, "meshtastic.receive")
        pub.subscribe(self.on_connection, "meshtastic.connection.established")
        pub.subscribe(self.on_lost, "meshtastic.connection.lost")

    def get_available_ports(self):
        """Returns a list of available serial ports."""
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def connect(self, port):
        """Connects to the specified serial port."""
        try:
            if self.interface:
                self.interface.close()
            
            # The library attempts auto-bauding or uses default.
            # If explicit baud rate looping is needed, we'd have to handle it at the stream level, 
            # but SerialInterface manages the stream creation.
            # We'll rely on SerialInterface's robust connection logic first.
            self.interface = meshtastic.serial_interface.SerialInterface(devPath=port)
            self.connected = True
            
            # Re-subscribe if needed, though usually pubsub persists. 
            # But we might need to refresh node list.
            self.nodes = self.interface.nodes
            try:
                self.my_node_info = self.interface.getMyNodeInfo()
            except:
                self.my_node_info = {}
                
            print(f"Connected to {port}")
            return True
        except Exception as e:
            print(f"Failed to connect to {port}: {e}")
            self.connected = False
            # Fallback to mock not strictly necessary here, but maybe user wants it off?
            # Keeping previous state or setting to disconnected is better.
            return False

    def disconnect(self):
        """Disconnects the current interface."""
        if self.interface:
            try:
                self.interface.close()
            except Exception as e:
                print(f"Error closing interface: {e}")
            self.interface = None
        self.connected = False
        self.nodes = {}
        self.my_node_info = {}
        print("Disconnected")

    def on_meshtastic_message(self, packet, interface):
        # Handle incoming messages
        if 'decoded' in packet:
            decoded = packet['decoded']
            if 'text' in decoded:
                try:
                    text = decoded['text']
                    sender = packet.get('from')
                    to = packet.get('to')
                    portnum = decoded.get('portnum') # TEXT_MESSAGE_APP = 1
                    
                    # Determine if it's a DM or Broadcast
                    # In Meshtastic, broadcasts are usually to ^all or a channel index is implied?
                    # If 'to' is a specific node ID, it's a DM.
                    # If 'to' is ^all (broadcast address), it's a broadcast.
                    # Actually, packet 'to' field is a node ID. 
                    # Broadcast ID is 0xFFFFFFFF (4294967295)
                    
                    is_broadcast = (to == 4294967295)
                    
                    timestamp = packet.get('rxTime', time.time())
                    
                    msg_obj = {
                        'from': sender,
                        'to': to,
                        'text': text,
                        'time': timestamp,
                        'is_self': False # Incoming
                    }
                    
                    if is_broadcast:
                        # For simplicity, assign to channel 0 ("Primary") if channel index not explicitly found
                        # In real packets, 'channel' key might be present in packet top level or decoded?
                        # Using 0 for now as main chat.
                        channel_idx = 0 
                        if 'channel' in packet:
                            channel_idx = packet['channel']
                            
                        if channel_idx not in self.chats['channels']:
                            self.chats['channels'][channel_idx] = []
                        self.chats['channels'][channel_idx].append(msg_obj)
                        
                    else:
                        # Direct Message
                        # Store under the sender's ID so we see it in our DM list with them.
                        # Important: ensure sender is treated consistently (int vs string).
                        # Sender in packet is usually int.
                        
                        # Use my_info to check if I am the sender (shouldn't happen in RX unless echo)
                        # but just in case. 
                        
                        other_node = sender
                        if other_node not in self.chats['dms']:
                            self.chats['dms'][other_node] = []
                        self.chats['dms'][other_node].append(msg_obj)
                        print(f"DM Received from {other_node}: {text}") # Debug log
                        
                    # Detect Chess Packet (JSON)
                    # Try parse
                    if text.strip().startswith('{') and '"chess":' in text:
                         try:
                             payload = json.loads(text)
                             if 'chess' in payload:
                                 # Publish chess event
                                 pub.sendMessage('chess.packet', payload=payload, sender=other_node)
                                 print(f"Chess packet detected from {other_node}")
                         except json.JSONDecodeError:
                             pass
                        
                except KeyError:
                    pass

        # Handle Traceroute responses
        if 'decoded' in packet:
            decoded = packet['decoded']
            # DEBUG: Dump keys to identify trace packet
            # print(f"DEBUG RX Packet Decoded: {decoded}") 
            
            # Check for ROUTING_APP (PortNum=34) or ADMIN_APP?
            # TraceRoute is often portnum=3? Or part of ROUTING?
            # Meshtastic lib usually handles parsing into 'route' if it's a valid trace response.
            
            if 'requestId' in decoded and 'route' in decoded:
                 # This is a trace response
                 route = decoded['route']
                 sender = packet.get('from')
                 self.traces[sender] = route
                 print(f"Trace received from {sender}: {route}")
            
            # Fallback debug: check for portnum 3 (TRACEROUTE) or 34 (ROUTING)
            portnum = decoded.get('portnum')
            if portnum in [3, 34]:
                 print(f"DEBUG: Routing/Trace packet from {packet.get('from')}: {decoded}")


    def on_connection(self, interface, topic=pub.AUTO_TOPIC):
        self.connected = True
        print("Connected to Meshtastic device")

    def on_lost(self, interface, topic=pub.AUTO_TOPIC):
        self.connected = False
        print("Lost connection to Meshtastic device")

    def send_message(self, text, destinationId=None, channelIndex=0):
        """
        Send a message. 
        destinationId: Node ID for DM. None for Broadcast.
        channelIndex: Channel index for Broadcast.
        """
        if self.interface:
            if destinationId:
                # Direct Message
                self.interface.sendText(text, destinationId=destinationId)
                # Store locally
                msg_obj = {
                    'from': self.my_node_info.get('user', {}).get('id'), # Should be my ID
                    'to': destinationId,
                    'text': text,
                    'time': time.time(),
                    'is_self': True
                }
                # For DMs, we assume destinationId is an integer if passed from GUI, or string?
                # Serial interface expects numeric node ID usually, or string?
                # It handles both, but let's be safe.
                
                # Store under the *other* person's ID
                if destinationId not in self.chats['dms']:
                    self.chats['dms'][destinationId] = []
                self.chats['dms'][destinationId].append(msg_obj)
                
            else:
                # Broadcast
                self.interface.sendText(text, channelIndex=channelIndex)
                # Store locally
                msg_obj = {
                    'from': self.my_node_info.get('user', {}).get('id'),
                    'to': 'Broadcast',
                    'text': text,
                    'time': time.time(),
                    'is_self': True
                }
                if channelIndex not in self.chats['channels']:
                    self.chats['channels'][channelIndex] = []
                self.chats['channels'][channelIndex].append(msg_obj)

    def send_trace_route(self, dest_node_id):
        """Sends a trace route request to the destination node."""
        if self.interface:
            self.interface.sendTraceRoute(dest_node_id, hopLimit=7) # Default hop limit

    def get_trace(self, node_id):
        return self.traces.get(node_id, [])

    def get_telemetry(self, node_id):
        """Retrieves telemetry (battery, chutil, etc) for a node."""
        if not self.interface or not self.nodes:
            return {}
            
        # Check if node exists
        node = self.nodes.get(node_id)
        if not node:
            # Check if it's us (sometimes we are not in the node list in the same way)
            my_info = self.interface.getMyNodeInfo()
            if my_info and my_info.get('user', {}).get('id') == node_id:
                # Local Node Logic
                 metrics = {}
                 if hasattr(self.interface, 'localNode'):
                      # Get Telemetry
                      t = getattr(self.interface.localNode, 'telemetry', {})
                      if t: metrics.update(t)
                      
                      # Get Position (Sats)
                      p = getattr(self.interface.localNode, 'position', {})
                      if p and 'satsVisible' in p:
                           metrics['sats'] = p['satsVisible']
                           
                 return metrics
            return {}

        # Look for deviceMetrics in the node dictionary
        # The 'node' object from interface.nodes values is usually a dict if retrieved via .nodes?
        # Actually meshtastic python stores it as a dictionary.
        
        metrics = {}
        if 'deviceMetrics' in node:
            metrics = node['deviceMetrics']
            
        return metrics

    def get_channels(self):
        """Returns a list of configured channels [ {index, name, role}, ... ]"""
        channels = []
        if self.interface and hasattr(self.interface, 'localNode'):
             # iterate over self.interface.localNode.channels
             # This is a list of Channel objects (protobuf)
             for ch in self.interface.localNode.channels:
                 if ch.role: # if it has a role, it exists
                     # Try to get name from settings
                     name = "Unknown"
                     if ch.settings and ch.settings.name:
                         name = ch.settings.name
                     elif ch.index == 0:
                         name = "Primary"
                     else:
                         name = f"Ch {ch.index}"
                    
                     # Extract more settings
                     uplink = getattr(ch.settings, 'uplink_enabled', True)
                     downlink = getattr(ch.settings, 'downlink_enabled', True)
                     # PSK might be bytes
                     psk = "********" # Hide by default
                         
                     channels.append({
                         'index': ch.index,
                         'name': name,
                         'role': ch.role,
                         'uplink': uplink,
                         'downlink': downlink,
                         'psk': psk
                     })
        
        # Sort by index
        channels.sort(key=lambda x: x['index'])
        if not channels:
            # Fallback if no connection or checks fail
            channels.append({'index': 0, 'name': 'Primary', 'role': 1})
            
        return channels

    def get_nodes(self):
        if self.interface:
            return self.interface.nodes
        return {}

    def get_my_info(self):
        if self.interface:
            return self.interface.getMyNodeInfo()
        return {}
        
    def haversine(self, lat1, lon1, lat2, lon2):
        """Calculates distance in meters between two lat/lon points."""
        try:
            R = 6371000 # Earth radius in meters
            phi1 = math.radians(lat1)
            phi2 = math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlambda = math.radians(lon2 - lon1)
            
            a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2) * math.sin(dlambda/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            return R * c
        except Exception:
            return 999999999 # Far away


    def close(self):
        if self.interface:
            try:
                self.interface.close()
            except Exception as e:
                pass # Suppress errors on exit




