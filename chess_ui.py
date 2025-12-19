
import customtkinter
import subprocess
import json
from pubsub import pub
from chess_engine import GameState, Move

class ChessBoardFrame(customtkinter.CTkFrame):
    def __init__(self, master, mesh_interface=None, width=400, height=500):
        super().__init__(master, width=width, height=height)
        
        self.mesh_interface = mesh_interface
        self.game_state = GameState()
        self.valid_moves = self.game_state.get_valid_moves()
        self.status_var = customtkinter.StringVar(value="Select Opponent or Play Local")
        
        # Multiplayer State
        self.is_multiplayer = False
        self.opponent_id = None
        self.my_color = "w" # 'w' or 'b'
        self.pending_invite = None # Node ID of pending invite
        
        # Subscribe to chess events
        pub.subscribe(self.on_chess_packet, 'chess.packet')
        
        # Piece Map (Unicode)
        self.pieces = {
            "wK": "♔", "wQ": "♕", "wR": "♖", "wB": "♗", "wN": "♘", "wP": "♙",
            "bK": "♚", "bQ": "♛", "bR": "♜", "bB": "♝", "bN": "♞", "bP": "♟",
            "--": "" 
        }
        
        # State
        self.selected_sq = () # (row, col)
        self.player_clicks = [] # [(r,c), (r,c)]
        
        # Grid Configuration
        self.buttons = [[None for _ in range(8)] for _ in range(8)]
        
        # --- UI Layout ---
        
        # 1. Header (Controls)
        self.header_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=10, pady=5)
        
        self.lbl_status = customtkinter.CTkLabel(self.header_frame, textvariable=self.status_var, font=("Arial", 14, "bold"))
        self.lbl_status.pack(pady=2)
        
        # Opponent Selector
        self.opponent_options = ["Local (Both Sides)"]
        self.var_opponent = customtkinter.StringVar(value=self.opponent_options[0])
        self.combo_opponent = customtkinter.CTkComboBox(self.header_frame, variable=self.var_opponent, values=self.opponent_options, width=160)
        self.combo_opponent.pack(side="left", padx=5)
        
        # Invite/Refresh
        self.btn_invite = customtkinter.CTkButton(self.header_frame, text="Invite", width=60, command=self.send_invite, fg_color="#4B7BE5")
        self.btn_invite.pack(side="left", padx=2)
        
        self.btn_refresh = customtkinter.CTkButton(self.header_frame, text="⟳", width=30, command=self.refresh_nodes)
        self.btn_refresh.pack(side="left", padx=2)
        
        self.btn_accept = customtkinter.CTkButton(self.header_frame, text="Accept Invite", width=80, fg_color="green", command=self.accept_invite)
        # Hidden by default
        
        # 2. Board Container
        self.board_frame = customtkinter.CTkFrame(self)
        self.board_frame.pack(padx=10, pady=10)
        
        # Draw Board
        self.draw_board()
        self.refresh_nodes()

    def refresh_nodes(self):
        if not self.mesh_interface: return
        nodes = self.mesh_interface.get_nodes()
        opts = ["Local (Both Sides)"]
        for nid, data in nodes.items():
            name = data.get('user', {}).get('shortName', str(nid))
            opts.append(f"{name} ({nid})")
        self.opponent_options = opts
        self.combo_opponent.configure(values=opts)
        self.combo_opponent.set(opts[0])

    def get_selected_node_id(self):
        val = self.var_opponent.get()
        if "Local" in val: return None
        # Extract ID from "Name (ID)"
        try:
            return val.split('(')[-1].strip(')')
        except:
            return None

    def send_invite(self):
        target = self.get_selected_node_id()
        if not target:
            self.status_var.set("Select a node first!")
            return
            
        # Send Invite JSON
        payload = {"chess": "invite"}
        self.send_json(target, payload)
        self.status_var.set(f"Invite sent to {target}...")
        self.opponent_id = target
        self.is_multiplayer = True # Tentative
        self.my_color = "w" # Inviter plays White

    def accept_invite(self):
        if not self.pending_invite: return
        
        # Send Accept
        payload = {"chess": "accept"}
        self.send_json(self.pending_invite, payload)
        
        self.opponent_id = self.pending_invite
        self.is_multiplayer = True
        self.my_color = "b" # Accepter plays Black
        self.status_var.set(f"Accepted! Playing vs {self.opponent_id}")
        self.pending_invite = None
        self.btn_accept.pack_forget()
        
        # Reset Game
        self.game_state = GameState()
        self.valid_moves = self.game_state.get_valid_moves()
        self.update_pieces()
        self.draw_board() # Re-draw for orientation

    def send_json(self, target, payload):
        if not self.mesh_interface: return
        import threading
        
        def _send():
            json_str = json.dumps(payload)
            # Send as DM
            try:
                 target_id = int(target)
            except:
                 target_id = target
            self.mesh_interface.send_message(json_str, destinationId=target_id)
            
        threading.Thread(target=_send, daemon=True).start()

    def on_chess_packet(self, payload, sender):
        # Handle Incoming JSON
        type = payload.get('chess')
        if type == 'invite':
            self.pending_invite = sender
            name = sender # lookup name if possible
            self.status_var.set(f"Invite from {name}!")
            self.btn_accept.pack(side="right", padx=5)
            
        elif type == 'accept':
            if str(sender) == str(self.opponent_id):
                self.status_var.set(f"{sender} accepted! You are White.")
                # Start game
                self.game_state = GameState()
                self.valid_moves = self.game_state.get_valid_moves()
                self.update_pieces()
                
        elif type == 'move':
            # Apply Move
            uci = payload.get('u')
            if uci:
                move = self.game_state.move_from_uci(uci)
                if move and move in self.valid_moves:
                    self.game_state.make_move(move)
                    self.play_sound(move.piece_captured != "--")
                    self.valid_moves = self.game_state.get_valid_moves()
                    self.update_pieces()
                    self.status_var.set("Your Turn")
                
        elif type == 'resign':
             self.status_var.set("Opponent Resigned!")

    def draw_board(self):
        # Clear existing
        for widget in self.board_frame.winfo_children():
            widget.destroy()
            
        self.buttons = [[None for _ in range(8)] for _ in range(8)]
        
        # Orientation Logic
        # White (default): Rows 0-7 drawn as 0 at top? No.
        # Standard printed board: Rank 8 (Row 0) at top. Rank 1 (Row 7) at bottom.
        # My GameState: Row 0 is Black (Top). Row 7 is White (Bottom).
        # So "Standard" is iterating r from 0 to 7. 
        
        rows = range(8)
        cols = range(8)
        
        if self.is_multiplayer and self.my_color == 'b':
            # Flip POV: Row 7 (White) at Top. Row 0 (Black) at Bottom.
            rows = range(7, -1, -1)
            # Columns also flip? usually POV flips both.
            # Black POV: h8 (0,7) is bottom-left? No.
            # Let's keep it simple: Just flip Rows?
            # Standard Black view: Rank 1 (Row 7) Top. Rank 8 (Row 0) Bottom.
            # e1 (7,4) is top. e8 (0,4) is bottom.
            # The columns: h (7) is Left? a (0) is Right?
            # Yes, standard POV flip reverses both axes (rotate 180).
            rows = range(7, -1, -1)
            cols = range(7, -1, -1)
        
        for r_disp, r_actual in enumerate(rows):
            for c_disp, c_actual in enumerate(cols):
                color = "#DDB88C" if (r_actual+c_actual)%2 == 0 else "#A66D4F"
                btn = customtkinter.CTkButton(self.board_frame, text="", 
                                              width=45, height=45, 
                                              fg_color=color, hover_color="#C0C0C0",
                                              corner_radius=0,
                                              font=("Arial", 30),
                                              command=lambda r=r_actual, c=c_actual: self.on_square_clicked(r, c))
                # Grid needs to be 0..7
                btn.grid(row=r_disp, column=c_disp)
                self.buttons[r_actual][c_actual] = btn
        self.update_pieces()

    def update_pieces(self):
        for r in range(8):
            for c in range(8):
                piece = self.game_state.board[r][c]
                symbol = self.pieces.get(piece, "")
                self.buttons[r][c].configure(text=symbol, text_color="black")
                
    def highlight_squares(self):
        # Reset colors
        for r in range(8):
            for c in range(8):
                color = "#DDB88C" if (r+c)%2 == 0 else "#A66D4F"
                self.buttons[r][c].configure(fg_color=color)
        
        # Highlight selected piece
        if self.selected_sq:
            r, c = self.selected_sq
            self.buttons[r][c].configure(fg_color="#6A9955") 
            
        # Highlight moves
        if self.selected_sq:
            r, c = self.selected_sq
            for move in self.valid_moves:
                if move.start_row == r and move.start_col == c:
                    self.buttons[move.end_row][move.end_col].configure(fg_color="#82C26E") 

    def on_square_clicked(self, r, c):
        # Turn Check for Multiplayer
        if self.is_multiplayer:
            is_white_turn = self.game_state.white_to_move
            if (self.my_color == 'w' and not is_white_turn) or (self.my_color == 'b' and is_white_turn):
                self.status_var.set("Wait for opponent...")
                return
            # Prevent moving opponent pieces
            piece = self.game_state.board[r][c]
            if not self.selected_sq: # Starting selection
                 if piece == "--": return
                 # Only select my pieces
                 p_color = piece[0] # 'w' or 'b'
                 if p_color != self.my_color:
                      return
        
        if self.selected_sq == (r, c):
            self.selected_sq = ()
            self.player_clicks = []
        else:
            self.selected_sq = (r, c)
            self.player_clicks.append(self.selected_sq)
            
        if len(self.player_clicks) == 2:
            move = Move(self.player_clicks[0], self.player_clicks[1], self.game_state.board)
            if move in self.valid_moves:
                self.game_state.make_move(move)
                self.play_sound(move.piece_captured != "--")
                
                # Send Move if Multiplayer
                if self.is_multiplayer:
                     uci = move.get_chess_notation()
                     self.send_json(self.opponent_id, {"chess": "move", "u": uci})
                
                self.valid_moves = self.game_state.get_valid_moves()
                self.selected_sq = ()
                self.player_clicks = []
                self.update_pieces()
                
                turn = "White" if self.game_state.white_to_move else "Black"
                self.status_var.set(f"{turn}'s Turn")
                
            else:
                self.player_clicks = [self.selected_sq]
                
        self.highlight_squares()

    def play_sound(self, is_capture):
        sound = "Hero" if is_capture else "Tink"
        try:
            subprocess.Popen(["afplay", f"/System/Library/Sounds/{sound}.aiff"])
        except:
            pass
