from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import mido
from mido import Message
import time

# Initialize FastMCP server
mcp = FastMCP("weather")
output_port = mido.open_output('loopMIDI Port 2') 

# MIDI Note mappings for FL Studio commands
NOTE_PLAY = 60          # C3
NOTE_STOP = 61          # C#3
NOTE_RECORD = 62        # D3
NOTE_NEW_PROJECT = 63   # D#3
NOTE_SET_BPM = 64       # E3
NOTE_NEW_PATTERN = 65   # F3
NOTE_SELECT_PATTERN = 66  # F#3
NOTE_ADD_CHANNEL = 67   # G3
NOTE_NAME_CHANNEL = 68  # G#3
NOTE_ADD_NOTE = 69      # A3
NOTE_ADD_TO_PLAYLIST = 70  # A#3
NOTE_SET_PATTERN_LEN = 71  # B3
NOTE_CHANGE_TEMPO = 72 

# Define custom MIDI CC messages for direct step sequencer grid control
CC_SELECT_CHANNEL = 100  # Select which channel to edit
CC_SELECT_STEP = 110     # Select which step to edit
CC_TOGGLE_STEP = 111     # Toggle the selected step on/off
CC_STEP_VELOCITY = 112   # Set velocity for the selected step

# Drum sound MIDI notes
KICK = 36      # C1
SNARE = 38     # D1
CLAP = 39      # D#1
CLOSED_HAT = 42  # F#1
OPEN_HAT = 46  # A#1



@mcp.tool()
def list_midi_ports():
    """List all available MIDI input ports"""
    print("\nAvailable MIDI Input Ports:")
    input_ports = mido.get_output_names()
    if not input_ports:
        print("  No MIDI input ports found")
    else:
        for i, port in enumerate(input_ports):
            print(f"  {i}: {port}")
    
    return input_ports

@mcp.tool()
def play():
    """Send MIDI message to start playback in FL Studio"""
    # Send Note On for C3 (note 60)
    output_port.send(mido.Message('note_on', note=60, velocity=100))
    time.sleep(0.1)  # Small delay
    output_port.send(mido.Message('note_off', note=60, velocity=0))
    print("Sent Play command")

@mcp.tool()
def stop():
    """Send MIDI message to stop playback in FL Studio"""
    # Send Note On for C#3 (note 61)
    output_port.send(mido.Message('note_on', note=61, velocity=100))
    time.sleep(0.1)  # Small delay
    output_port.send(mido.Message('note_off', note=61, velocity=0))
    print("Sent Stop command")

def int_to_midi_bytes(value):
    """
    Convert an integer value into an array of MIDI-compatible bytes (7-bit values)
    
    Args:
        value (int): The integer value to convert
        
    Returns:
        list: Array of MIDI bytes (each 0-127)
    """
    if value < 0:
        print("Warning: Negative values not supported, converting to positive")
        value = abs(value)
    
    # Special case for zero
    if value == 0:
        return [0]
    
    # Convert to MIDI bytes (7-bit values, MSB first)
    midi_bytes = []
    while value > 0:
        # Extract the lowest 7 bits and prepend to array
        midi_bytes.insert(0, value & 0x7F)  # 0x7F = 127 (binary: 01111111)
        # Shift right by 7 bits
        value >>= 7
    
    return midi_bytes

@mcp.tool()
def change_tempo(bpm):
    """
    Change the tempo in FL Studio using a sequence of MIDI notes
    
    This function converts a BPM value to an array of MIDI notes,
    sends a start marker, the notes, and an end marker to trigger
    a tempo change in FL Studio.
    
    Args:
        bpm (float): The desired tempo in beats per minute
    """
    # Ensure BPM is within a reasonable range
    if bpm < 20 or bpm > 999:
        print(f"Warning: BPM value {bpm} is outside normal range (20-999)")
        bpm = max(20, min(bpm, 999))
    
    # Convert BPM to integer
    bpm_int = int(bpm)
    
    # Convert to MIDI bytes
    midi_notes = int_to_midi_bytes(bpm_int)
    
    print(f"Setting tempo to {bpm_int} BPM using note array: {midi_notes}")
    
    # Send start marker (note 72)
    send_midi_note(72)
    time.sleep(0.2)
    
    # Send each note in the array
    for note in midi_notes:
        send_midi_note(note)
        time.sleep(0.1)
    
    # Send end marker (note 73)
    send_midi_note(73)
    time.sleep(0.2)
    
    print(f"Tempo change to {bpm_int} BPM sent successfully using {len(midi_notes)} notes")

@mcp.tool()
def record():
    """Send MIDI message to start recording in FL Studio"""
    # Send Note On for D3 (note 62)
    output_port.send(mido.Message('note_on', note=62, velocity=100))
    time.sleep(0.1)  # Small delay
    output_port.send(mido.Message('note_off', note=62, velocity=0))
    print("Sent Record command")

# @mcp.tool()
# def send_melody(notes_data):
#     """
#     Send a sequence of MIDI notes with timing information to FL Studio for recording
    
#     Args:
#         notes_data (str): String containing note data in format "note,velocity,length,position"
#                          with each note on a new line
#     """
#     # Constants for special MIDI messages
#     TOGGLE_RECEIVE = 0      # Toggle receiving mode on/off
#     DECIMAL_MARKER = 100    # Indicates next value is a decimal part
#     LENGTH_MARKER = 101     # Next value affects length
#     POSITION_MARKER = 102   # Next value affects position
    
#     # Parse the notes_data string
#     notes = []
#     for line in notes_data.strip().split('\n'):
#         if not line.strip():
#             continue
            
#         parts = line.strip().split(',')
#         if len(parts) != 4:
#             print(f"Warning: Skipping invalid line: {line}")
#             continue
            
#         try:
#             note = int(parts[0])
#             velocity = int(parts[1])
#             length = float(parts[2])
#             position = float(parts[3])
#             notes.append((note, velocity, length, position))
#         except ValueError:
#             print(f"Warning: Skipping line with invalid values: {line}")
#             continue
    
#     # Count total MIDI messages we'll send
#     # For each note: note+velocity, length marker, length whole, length decimal part (if needed),
#     # position marker, position whole, position decimal part (if needed)
#     midi_message_count = 0
#     for note, velocity, length, position in notes:
#         # Basic note and its parameters
#         midi_message_count += 1  # Note itself
#         midi_message_count += 1  # Length marker
#         midi_message_count += 1  # Length whole part
        
#         # Add decimal parts if needed
#         if length != int(length):
#             midi_message_count += 2  # Decimal marker + decimal value
            
#         midi_message_count += 1  # Position marker
#         midi_message_count += 1  # Position whole part
        
#         # Add decimal parts if needed  
#         if position != int(position):
#             midi_message_count += 2  # Decimal marker + decimal value
    
#     # Start receiving mode and send count
#     print(f"Starting FL Studio note receiving mode with {midi_message_count} messages...")
#     send_midi_note(TOGGLE_RECEIVE)
#     time.sleep(0.2)
    
#     # Send count of messages
#     send_midi_note(midi_message_count)
#     time.sleep(0.2)
    
#     # Process each note
#     for i, (note, velocity, length, position) in enumerate(notes):
#         print(f"Sending note {i+1}/{len(notes)}: note={note}, velocity={velocity}, length={length:.2f}, position={position:.2f}")
        
#         # Send the note and velocity
#         send_midi_note(note, velocity)
#         time.sleep(0.1)
        
#         # Send length parameter
#         send_midi_note(LENGTH_MARKER)
#         time.sleep(0.1)
        
#         # Split length into whole and decimal parts
#         length_whole = int(length)
#         length_decimal = int((length - length_whole) * 10 + 0.5)  # Round to nearest
        
#         # Send whole part
#         send_midi_note(length_whole)
#         time.sleep(0.1)
        
#         # Send decimal part if non-zero
#         if length_decimal > 0:
#             send_midi_note(DECIMAL_MARKER)
#             time.sleep(0.1)
#             send_midi_note(length_decimal)
#             time.sleep(0.1)
        
#         # Send position parameter
#         send_midi_note(POSITION_MARKER)
#         time.sleep(0.1)
        
#         # Split position into whole and decimal parts
#         position_whole = int(position)
#         position_decimal = int((position - position_whole) * 10 + 0.5)  # Round to nearest
        
#         # Send whole part
#         send_midi_note(position_whole)
#         time.sleep(0.1)
        
#         # Send decimal part if non-zero
#         if position_decimal > 0:
#             send_midi_note(DECIMAL_MARKER)
#             time.sleep(0.1)
#             send_midi_note(position_decimal)
#             time.sleep(0.1)
    
#     print(f"Successfully sent {len(notes)} notes to FL Studio")
#     return f"Sent {len(notes)} notes ({midi_message_count} MIDI messages) to FL Studio for recording"

# @mcp.tool()
# def send_melody(notes_data):
#     """
#     Send a sequence of MIDI notes with timing information to FL Studio for recording
    
#     Args:
#         notes_data (str): String containing note data in format "note,velocity,length,position"
#                          with each note on a new line
#     """
#     # Constants for special MIDI messages
#     TOGGLE_RECEIVE = 0      # Toggle receiving mode on/off
#     DECIMAL_MARKER = 100    # Indicates next value is a decimal part
#     LENGTH_MARKER = 101     # Next value affects length
#     POSITION_MARKER = 102   # Next value affects position
    
#     # Parse the notes_data string
#     notes = []
#     for line in notes_data.strip().split('\n'):
#         if not line.strip():
#             continue
            
#         parts = line.strip().split(',')
#         if len(parts) != 4:
#             print(f"Warning: Skipping invalid line: {line}")
#             continue
            
#         try:
#             note = int(parts[0])
#             velocity = int(parts[1])
#             length = float(parts[2])
#             position = float(parts[3])
#             notes.append((note, velocity, length, position))
#         except ValueError:
#             print(f"Warning: Skipping line with invalid values: {line}")
#             continue
    
#     # Calculate total number of MIDI messages
#     midi_message_count = 0
#     for note, velocity, length, position in notes:
#         # Basic note message
#         midi_message_count += 1  # Note/velocity
        
#         # Length messages
#         midi_message_count += 1  # LENGTH_MARKER
#         midi_message_count += 1  # Length whole part
#         if length != int(length):
#             midi_message_count += 1  # DECIMAL_MARKER
#             midi_message_count += 1  # Decimal value
        
#         # Position messages
#         midi_message_count += 1  # POSITION_MARKER
#         midi_message_count += 1  # Position whole part
#         if position != int(position):
#             midi_message_count += 1  # DECIMAL_MARKER
#             midi_message_count += 1  # Decimal value
    
#     print(f"Starting MIDI transfer for {len(notes)} notes ({midi_message_count} messages)")
    
#     # Send toggle receive command
#     output_port.send(mido.Message('note_on', note=TOGGLE_RECEIVE, velocity=100))
#     time.sleep(0.1)
#     output_port.send(mido.Message('note_off', note=TOGGLE_RECEIVE, velocity=0))
#     time.sleep(0.2)
    
#     # Send message count
#     output_port.send(mido.Message('note_on', note=min(midi_message_count, 127), velocity=100))
#     time.sleep(0.1)
#     output_port.send(mido.Message('note_off', note=min(midi_message_count, 127), velocity=0))
#     time.sleep(0.2)
    
#     # Send each note
#     for i, (note, velocity, length, position) in enumerate(notes):
#         print(f"Sending note {i+1}/{len(notes)}: note={note}, velocity={velocity}, length={length:.2f}, position={position:.2f}")
        
#         # Send note and velocity
#         output_port.send(mido.Message('note_on', note=note, velocity=velocity))
#         time.sleep(0.1)
#         output_port.send(mido.Message('note_off', note=note, velocity=0))
#         time.sleep(0.1)
        
#         # Send length
#         output_port.send(mido.Message('note_on', note=LENGTH_MARKER, velocity=100))
#         time.sleep(0.1)
#         output_port.send(mido.Message('note_off', note=LENGTH_MARKER, velocity=0))
#         time.sleep(0.1)
        
#         # Length whole part 
#         length_whole = int(length)
#         output_port.send(mido.Message('note_on', note=length_whole, velocity=100))
#         time.sleep(0.1)
#         output_port.send(mido.Message('note_off', note=length_whole, velocity=0))
#         time.sleep(0.1)
        
#         # Length decimal part if needed
#         if length != length_whole:
#             length_decimal = int((length - length_whole) * 10 + 0.5)  # Round to nearest
            
#             output_port.send(mido.Message('note_on', note=DECIMAL_MARKER, velocity=100))
#             time.sleep(0.1)
#             output_port.send(mido.Message('note_off', note=DECIMAL_MARKER, velocity=0))
#             time.sleep(0.1)
            
#             output_port.send(mido.Message('note_on', note=length_decimal, velocity=100))
#             time.sleep(0.1)
#             output_port.send(mido.Message('note_off', note=length_decimal, velocity=0))
#             time.sleep(0.1)
        
#         # Send position
#         output_port.send(mido.Message('note_on', note=POSITION_MARKER, velocity=100))
#         time.sleep(0.1)
#         output_port.send(mido.Message('note_off', note=POSITION_MARKER, velocity=0))
#         time.sleep(0.1)
        
#         # Position whole part
#         position_whole = int(position)
#         output_port.send(mido.Message('note_on', note=position_whole, velocity=100))
#         time.sleep(0.1)
#         output_port.send(mido.Message('note_off', note=position_whole, velocity=0))
#         time.sleep(0.1)
        
#         # Position decimal part if needed
#         if position != position_whole:
#             position_decimal = int((position - position_whole) * 10 + 0.5)  # Round to nearest
            
#             output_port.send(mido.Message('note_on', note=DECIMAL_MARKER, velocity=100))
#             time.sleep(0.1)
#             output_port.send(mido.Message('note_off', note=DECIMAL_MARKER, velocity=0))
#             time.sleep(0.1)
            
#             output_port.send(mido.Message('note_on', note=position_decimal, velocity=100))
#             time.sleep(0.1)
#             output_port.send(mido.Message('note_off', note=position_decimal, velocity=0))
#             time.sleep(0.1)
        
#         # Add a small delay between notes to make sure FL Studio has time to process
#         time.sleep(0.1)
    
#     print(f"Successfully sent {len(notes)} notes to FL Studio")
#     return f"Sent {len(notes)} notes ({midi_message_count} MIDI messages) to FL Studio for recording"


@mcp.tool()
def send_melody(notes_data):
    """
    Send a sequence of MIDI notes with timing information to FL Studio for recording
    
    Args:
        notes_data (str): String containing note data in format "note,velocity,length,position"
                         with each note on a new line
    """
    # Parse the notes_data string into a list of note tuples
    notes = []
    for line in notes_data.strip().split('\n'):
        if not line.strip():
            continue
            
        parts = line.strip().split(',')
        if len(parts) != 4:
            print(f"Warning: Skipping invalid line: {line}")
            continue
            
        try:
            note = min(127, max(0, int(parts[0])))
            velocity = min(127, max(0, int(parts[1])))
            length = max(0, float(parts[2]))
            position = max(0, float(parts[3]))
            notes.append((note, velocity, length, position))
        except ValueError:
            print(f"Warning: Skipping line with invalid values: {line}")
            continue
    
    if not notes:
        return "No valid notes found in input data"
    
    # Create the MIDI data array (5 values per note)
    midi_data = []
    for note, velocity, length, position in notes:
        # 1. Note value (0-127)
        midi_data.append(note)
        
        # 2. Velocity value (0-127)
        midi_data.append(velocity)
        
        # 3. Length whole part (0-127)
        length_whole = min(127, int(length))
        midi_data.append(length_whole)
        
        # 4. Length decimal part (0-9)
        length_decimal = int(round((length - length_whole) * 10)) % 10
        midi_data.append(length_decimal)
        
        # 5. Position whole part (0-127)
        position_whole = min(127, int(position))
        midi_data.append(position_whole)
        
        # 6. Position decimal part (0-9)
        position_decimal = int(round((position - position_whole) * 10)) % 10
        midi_data.append(position_decimal)
    
    # Start MIDI transfer
    print(f"Transferring {len(notes)} notes ({len(midi_data)} MIDI values)...")
    
    # Initial toggle signal (note 0)
    send_midi_note(0)
    time.sleep(0.01)
    
    # Send total count of notes
    send_midi_note(min(127, len(notes)))
    time.sleep(0.01)
    
    # Send all MIDI data values
    for i, value in enumerate(midi_data):
        send_midi_note(value)
        #time.sleep(0.1)
        #print(f"Sent MIDI value {i+1}/{len(midi_data)}: {value}")
    
    send_midi_note(127)

    #print(f"Melody transfer complete: {len(notes)} notes sent")
    return f"Melody successfully transferred: {len(notes)} notes ({len(midi_data)} MIDI values) sent to FL Studio"

# Send a MIDI note message
@mcp.tool()
def send_midi_note(note, velocity=1, duration=0.01):
    """Send a MIDI note on/off message with specified duration"""
    note_on = Message('note_on', note=note, velocity=velocity)
    output_port.send(note_on)
    #print(f"Sent MIDI note {note} (on), velocity {velocity}")
    time.sleep(duration)
    note_off = Message('note_off', note=note, velocity=0)
    output_port.send(note_off)
    print(f"Sent MIDI note {note} (off)")
    #time.sleep(0.1)  # Small pause between messages

# Send a MIDI CC message
@mcp.tool()
def send_midi_cc(control, value, channel=0):
    """Send a MIDI Control Change message"""
    if value > 127:
        print(f"Warning: Value {value} exceeds MIDI range (0-127)")
        value = 127
    cc = Message('control_change', channel=channel, control=control, value=value)
    output_port.send(cc)
    print(f"Sent CC: control={control}, value={value}")
    time.sleep(0.1)  # Small pause between messages

# Create a new channel with a name
@mcp.tool()
def create_channel(name):
    """Create a new channel in FL Studio with the specified name"""
    print(f"Creating channel: {name}")
    
    send_midi_note(NOTE_ADD_CHANNEL)
    time.sleep(0.5)  # Longer delay for channel creation
    
    send_midi_note(NOTE_NAME_CHANNEL)
    time.sleep(0.2)
    
    for char in name:
        send_midi_cc(2, ord(char))
        time.sleep(0.05)
    
    send_midi_cc(2, 0)  # Terminator
    time.sleep(0.5)
    print(f"Channel '{name}' created successfully")

# Set a specific step in the step sequencer grid
@mcp.tool()
def set_step(channel, step, enabled=True, velocity=100):
    """
    Set a step in the FL Studio step sequencer grid
    
    Args:
        channel: Channel index (0-based)
        step: Step index (0-15)
        enabled: Whether the step is active
        velocity: Velocity/level for the step (0-127)
    """
    print(f"Setting channel {channel}, step {step}, enabled={enabled}, velocity={velocity}")
    
    # Select the channel
    send_midi_cc(CC_SELECT_CHANNEL, channel)
    time.sleep(0.1)
    
    # Select the step
    send_midi_cc(CC_SELECT_STEP, step)
    time.sleep(0.1)
    
    # Enable/disable the step
    send_midi_cc(CC_TOGGLE_STEP, 1 if enabled else 0)
    time.sleep(0.1)
    
    # Set the velocity/level if the step is enabled
    if enabled:
        send_midi_cc(CC_STEP_VELOCITY, velocity)
        time.sleep(0.1)

# Create a simple 4/4 beat pattern
@mcp.tool()
def create_basic_beat():
    """Create a simple 4/4 beat pattern with kick, snare, and hi-hat"""
    print("Creating a new drum pattern in FL Studio's Step Sequencer...")
    
    # 1. Create a new project
    send_midi_note(NOTE_NEW_PROJECT)
    time.sleep(2.0)  # Longer delay for project creation
    
    # 2. Set BPM to 90
    send_midi_note(NOTE_SET_BPM)
    send_midi_cc(1, 90)
    time.sleep(0.5)
    
    # 3. Create a new pattern
    send_midi_note(NOTE_NEW_PATTERN)
    time.sleep(0.5)
    
    # 4. Create channels
    create_channel("Kick")      # Channel 0
    create_channel("Clap")      # Channel 1
    create_channel("Hi-Hat")    # Channel 2
    create_channel("Snare")     # Channel 3
    
    # 5. Create kick pattern (every quarter note)
    print("Setting kick pattern...")
    for step in [0, 4, 8, 12]:  # Steps on beats 1, 2, 3, 4
        set_step(0, step, True, 100)
        time.sleep(0.2)
    
    # 6. Create clap pattern (beats 2 and 4)
    print("Setting clap pattern...")
    for step in [4, 12]:  # Steps on beats 2 and 4
        set_step(1, step, True, 90)
        time.sleep(0.2)
    
    # 7. Create hi-hat pattern (eighth notes)
    print("Setting hi-hat pattern...")
    for step in range(0, 16, 2):  # Steps on all eighth notes
        velocity = 90 if step % 4 == 0 else 70  # Accent on the beat
        set_step(2, step, True, velocity)
        time.sleep(0.2)
    
    # 8. Create snare pattern (beats 2 and 4)
    print("Setting snare pattern...")
    for step in [4, 12]:  # Steps on beats 2 and 4
        set_step(3, step, True, 95)
        time.sleep(0.2)
    
    # 9. Add pattern to playlist
    print("Adding pattern to playlist...")
    time.sleep(0.5)
    send_midi_note(NOTE_ADD_TO_PLAYLIST)
    time.sleep(0.2)
    send_midi_cc(10, 1)   # Pattern number
    time.sleep(0.1)
    send_midi_cc(11, 0)   # Position (0 bars)
    time.sleep(0.1)
    send_midi_cc(12, 0)   # Track 0
    time.sleep(0.5)
    
    # 10. Play the pattern
    print("Playing the pattern...")
    send_midi_note(NOTE_PLAY)
    
    print("Beat created successfully! You should see steps in the Channel Rack step sequencer.")

# Create a trap-style beat
@mcp.tool()
def create_trap_beat():
    """Create a trap-style beat with hi-hat rolls and 808 kicks"""
    print("Creating a trap beat in FL Studio's Step Sequencer...")
    
    # 1. Create a new project
    send_midi_note(NOTE_NEW_PROJECT)
    time.sleep(2.0)
    
    # 2. Set BPM to 140 (typical trap tempo)
    send_midi_note(NOTE_SET_BPM)
    send_midi_cc(1, 140)
    time.sleep(0.5)
    
    # 3. Create a new pattern
    send_midi_note(NOTE_NEW_PATTERN)
    time.sleep(0.5)
    
    # 4. Create channels
    create_channel("808 Kick")   # Channel 0
    create_channel("Clap")       # Channel 1
    create_channel("Hi-Hat")     # Channel 2
    create_channel("Open Hat")   # Channel 3
    create_channel("808 Bass")   # Channel 4
    
    # 5. Create 808 kick pattern (trap style with ghost notes)
    print("Setting 808 kick pattern...")
    for step, velocity in [(0, 100), (6, 80), (8, 100), (14, 90)]:
        set_step(0, step, True, velocity)
        time.sleep(0.2)
    
    # 6. Create clap pattern (beats 2 and 4)
    print("Setting clap pattern...")
    for step in [4, 12]:
        set_step(1, step, True, 95)
        time.sleep(0.2)
    
    # 7. Create hi-hat pattern (trap style with rolls)
    print("Setting hi-hat pattern...")
    # Simple 16th note pattern with velocity variations
    velocities = [90, 60, 75, 60, 90, 60, 75, 60, 90, 60, 75, 60, 90, 60, 75, 60]
    for step, velocity in enumerate(velocities):
        set_step(2, step, True, velocity)
        time.sleep(0.2)
    
    # 8. Create open hi-hat accents
    print("Setting open hi-hat pattern...")
    for step in [2, 10]:
        set_step(3, step, True, 85)
        time.sleep(0.2)
    
    # 9. Create 808 bass pattern
    print("Setting 808 bass pattern...")
    for step, velocity in [(0, 100), (8, 95)]:
        set_step(4, step, True, velocity)
        time.sleep(0.2)
    
    # 10. Add pattern to playlist
    print("Adding pattern to playlist...")
    time.sleep(0.5)
    send_midi_note(NOTE_ADD_TO_PLAYLIST)
    time.sleep(0.2)
    send_midi_cc(10, 1)   # Pattern number
    time.sleep(0.1)
    send_midi_cc(11, 0)   # Position (0 bars)
    time.sleep(0.1)
    send_midi_cc(12, 0)   # Track 0
    time.sleep(0.5)
    
    # 11. Play the pattern
    print("Playing the pattern...")
    send_midi_note(NOTE_PLAY)
    
    print("Trap beat created successfully! You should see steps in the Channel Rack step sequencer.")

# Create a house beat
@mcp.tool()
def create_house_beat():
    """Create a classic house beat with four-on-the-floor kick"""
    print("Creating a house beat in FL Studio's Step Sequencer...")
    
    # 1. Create a new project
    send_midi_note(NOTE_NEW_PROJECT)
    time.sleep(2.0)
    
    # 2. Set BPM to 128 (typical house tempo)
    send_midi_note(NOTE_SET_BPM)
    send_midi_cc(1, 128)
    time.sleep(0.5)
    
    # 3. Create a new pattern
    send_midi_note(NOTE_NEW_PATTERN)
    time.sleep(0.5)
    
    # 4. Create channels
    create_channel("Kick")       # Channel 0
    create_channel("Clap")       # Channel 1
    create_channel("Closed Hat") # Channel 2
    create_channel("Open Hat")   # Channel 3
    create_channel("Bass")       # Channel 4
    
    # 5. Create four-on-the-floor kick pattern
    print("Setting kick pattern...")
    for step in [0, 4, 8, 12]:
        set_step(0, step, True, 100)
        time.sleep(0.2)
    
    # 6. Create clap/snare on beats 2 and 4
    print("Setting clap pattern...")
    for step in [4, 12]:
        set_step(1, step, True, 90)
        time.sleep(0.2)
    
    # 7. Create closed hi-hat pattern (offbeats)
    print("Setting closed hi-hat pattern...")
    for step in [2, 6, 10, 14]:  # Offbeats
        set_step(2, step, True, 85)
        time.sleep(0.2)
    
    # 8. Create open hi-hat accents
    print("Setting open hi-hat pattern...")
    set_step(3, 7, True, 85)  # Single open hat accent
    time.sleep(0.2)
    
    # 9. Create simple bass pattern
    print("Setting bass pattern...")
    for step, velocity in [(0, 100), (4, 90), (8, 100), (12, 90)]:
        set_step(4, step, True, velocity)
        time.sleep(0.2)
    
    # 10. Add pattern to playlist
    print("Adding pattern to playlist...")
    time.sleep(0.5)
    send_midi_note(NOTE_ADD_TO_PLAYLIST)
    time.sleep(0.2)
    send_midi_cc(10, 1)   # Pattern number
    time.sleep(0.1)
    send_midi_cc(11, 0)   # Position (0 bars)
    time.sleep(0.1)
    send_midi_cc(12, 0)   # Track 0
    time.sleep(0.5)
    
    # 11. Play the pattern
    print("Playing the pattern...")
    send_midi_note(NOTE_PLAY)
    
    print("House beat created successfully! You should see steps in the Channel Rack step sequencer.")
    

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')