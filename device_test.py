# device_test.py
# name=Test Controller

import transport
import ui
import midi
import channels
import playlist
import patterns
import arrangement
import general
import device
import time
import sys

# Global variables
running = True
command_history = []
current_pattern = 0
current_channel = 0
terminal_active = False

collecting_tempo_notes = False
tempo_note_array = []
NOTE_TEMPO_START = 72  # C4 starts tempo note collection
NOTE_TEMPO_END = 73    # C#4 ends collection and applies tempo change

channel_to_edit = 0
step_to_edit = 0

def midi_notes_to_int(midi_notes):
    """
    Convert an array of MIDI note values (7 bits each) into a single integer
    
    This function takes a list of MIDI notes and combines them into a single
    integer value, with the first note being the most significant.
    
    Args:
        midi_notes (list): A list of MIDI note values (each 0-127)
        
    Returns:
        int: The combined integer value
    """
    result = 0
    for note in midi_notes:
        # Ensure each value is within MIDI range (0-127)
        note_value = min(127, max(0, note))
        # Shift left by 7 bits (MIDI values use 7 bits) and combine
        result = (result << 7) | note_value
    return result

def OnInit():
    """Called when the script is loaded by FL Studio"""
    print("FL Studio Terminal Beat Builder initialized")
    print("Type 'help' for a list of commands")
    
    return

def OnDeInit():
    """Called when the script is unloaded by FL Studio"""
    global running
    running = False  # Signal the terminal thread to exit
    print("FL Studio Terminal Beat Builder deinitialized")
    return

def OnRefresh(flags):
    """Called when FL Studio's state changes or when a refresh is needed"""
    # Update terminal with current state if needed
    return

def OnMidiIn(event):
    """Called whenever the device sends a MIDI message to FL Studio"""
    print(f"MIDI In - Status: {event.status}, Data1: {event.data1}, Data2: {event.data2}")
    return

def change_tempo(bpm):
    """
    Change the tempo in FL Studio to the specified BPM value
    
    Args:
        bpm (float): The desired tempo in beats per minute
    """
    # FL Studio stores tempo as BPM * 1000
    tempo_value = int(bpm * 1000)
    
    # Use processRECEvent to set the tempo
    # REC_Tempo is the event ID for tempo
    # REC_Control | REC_UpdateControl flags ensure the value is set and the UI updates
    general.processRECEvent(
        midi.REC_Tempo,
        tempo_value,
        midi.REC_Control | midi.REC_UpdateControl
    )




def OnMidiMsg(event, timestamp=0):
    """Called when a processed MIDI message is received"""
    print(f"MIDI Msg - Status: {event.status}, Data1: {event.data1}, Data2: {event.data2}")
    
    global channel_to_edit, step_to_edit
    global collecting_tempo_notes, tempo_note_array
    
    # Handle Note On messages
    if event.status >= midi.MIDI_NOTEON and event.status < midi.MIDI_NOTEON + 16 and event.data2 > 0:
        note = event.data1
        
        # Start collecting notes for tempo change
        if note == 72:
            collecting_tempo_notes = True
            tempo_note_array = []
            print("Started collecting notes for tempo change")
            event.handled = True
            
        # End collection and apply tempo change
        elif note == 73:
            if collecting_tempo_notes and tempo_note_array:
                bpm = change_tempo_from_notes(tempo_note_array)
                print(f"Tempo changed to {bpm} BPM from collected notes: {tempo_note_array}")
                collecting_tempo_notes = False
                tempo_note_array = []
            else:
                print("No tempo notes collected, tempo unchanged")
            event.handled = True
            
        # Collect notes for tempo if in collection mode
        elif collecting_tempo_notes:
            tempo_note_array.append(note)
            print(f"Added note {note} to tempo collection, current array: {tempo_note_array}")
            event.handled = True
    
    # Handle Control Change messages
    elif event.status >= midi.MIDI_CONTROLCHANGE and event.status < midi.MIDI_CONTROLCHANGE + 16:
        # CC 100: Select channel to edit
        if event.data1 == 100:
            channel_to_edit = event.data2
            channels.selectOneChannel(channel_to_edit)
            print(f"Selected channel {channel_to_edit} for grid editing")
            event.handled = True
            
        # CC 110: Select step to edit
        elif event.data1 == 110:
            step_to_edit = event.data2
            print(f"Selected step {step_to_edit} for grid editing")
            event.handled = True
            
        # CC 111: Toggle step on/off
        elif event.data1 == 111:
            enabled = event.data2 > 0
            channels.setGridBit(channel_to_edit, step_to_edit, enabled)
            print(f"Set grid bit for channel {channel_to_edit}, step {step_to_edit} to {enabled}")
            commit_pattern_changes()  # Force UI update
            event.handled = True
            
        # CC 112: Set step velocity/level
        elif event.data1 == 112:
            velocity = event.data2
            channels.setStepLevel(channel_to_edit, step_to_edit, velocity)
            print(f"Set step level for channel {channel_to_edit}, step {step_to_edit} to {velocity}")
            commit_pattern_changes()  # Force UI update
            event.handled = True
        
        # Process other CC messages
        else:
            # Handle other CC messages with your existing code...
            pass
    
    # Handle other MIDI message types if needed
    else:
        # Process other MIDI message types
        pass
    
    # Handle Note On messages with your existing code...
    # [rest of your existing OnMidiMsg function]

# Make sure your commit_pattern_changes function is defined:
def commit_pattern_changes(pattern_num=None):
    """Force FL Studio to update the pattern data visually"""
    if pattern_num is None:
        pattern_num = patterns.patternNumber()
    
    # Force FL Studio to redraw and commit changes
    ui.crDisplayRect()
    
    # Force channel rack to update
    ui.setFocused(midi.widChannelRack)
    
    # Update playlist if needed
    playlist.refresh()
def OnTransport(isPlaying):
    """Called when the transport state changes (play/stop)"""
    print(f"Transport state changed: {'Playing' if isPlaying else 'Stopped'}")
    return

def OnTempoChange(tempo):
    """Called when the tempo changes"""
    print(f"Tempo changed to: {tempo} BPM")
    return

def add_chord_to_piano_roll(midi_bytes, time_position=0, length=96):
    """
    Add a chord represented as MIDI bytes to the currently selected piano roll
    
    Format: [note_count, note1, note2, note3, ...]
    
    Args:
        midi_bytes: List of MIDI bytes (0-127)
        time_position (int): Starting position in ticks
        length (int): Note length in ticks (default is 96 for a quarter note)
    """
    if not midi_bytes or midi_bytes[0] < 1:
        print("Invalid midi byte array")
        return
    
    note_count = midi_bytes[0]
    
    # Get the currently selected channel
    channel = channels.selectedChannel()
    
    print(f"Adding chord to channel {channel} at position {time_position}")
    
    # Process each note in the chord
    for i in range(note_count):
        if i + 1 < len(midi_bytes):
            note = midi_bytes[i + 1]
            velocity = 100  # Default velocity
            pan = 0  # Center pan
            
            # Add the note to the piano roll
            channels.addNote(channel, time_position, length, note, velocity, pan)
            print(f"Added note {note} at position {time_position} with length {length}")
    
    # Force update the UI to show the new notes
    commit_pattern_changes()
    print(f"Chord with {note_count} notes added to piano roll")

# Terminal interface functions
def start_terminal_thread():
    """Start a thread to handle terminal input"""
    global terminal_active
    if not terminal_active:
        terminal_active = True
        thread = threading.Thread(target=terminal_loop)
        thread.daemon = True
        thread.start()

def terminal_loop():
    """Main terminal input loop"""
    global running, terminal_active
    
    print("\n===== FL STUDIO TERMINAL BEAT BUILDER =====")
    print("Enter commands to build your beat (type 'help' for commands)")
    
    while running:
        try:
            command = input("\nFLBEAT> ")
            command_history.append(command)
            process_command(command)
        except Exception as e:
            print(f"Error processing command: {e}")
    
    terminal_active = False

def record_c_major_chord_in_tempo(length_beats=4.0, position_beats=0.0):
    """
    Records a C major chord to the piano roll synced with project tempo
    
    Args:
        length_beats (float): Length of chord in beats (1.0 = quarter note)
        position_beats (float): Position to place chord in beats from start
    """
    # Make sure we're in recording mode and transport is stopped first
    if transport.isPlaying():
        transport.stop()
    
    if not transport.isRecording():
        transport.record()
    
    # Get the current channel
    channel = channels.selectedChannel()
    
    # Get the project's PPQ (pulses per quarter note)
    ppq = general.getRecPPQ()
    transport.setSongPos(0, 2)
    
    # Calculate ticks based on beats
    length_ticks = int(length_beats * ppq)
    position_ticks = int(position_beats * ppq)
    
    # Set playback position if needed
    if position_beats > 0:
        transport.setSongPos(position_ticks, 2)  # 2 = SONGLENGTH_ABSTICKS
    
    print(f"Recording C major chord to channel {channel}, length: {length_beats} beats")
    
    # Start playback - this begins recording
    transport.start()
    
    # Play the chord notes
    channels.midiNoteOn(channel, 60, 100)  # C
    channels.midiNoteOn(channel, 64, 100)  # E
    channels.midiNoteOn(channel, 67, 100)  # G
    
    # We can't use time.sleep() for tempo synchronization
    # Instead, we'll monitor the song position until we reach the end point
    start_pos = transport.getSongPos(2)  # Get current position in ticks
    end_pos = start_pos + length_ticks
    
    # Wait until we reach the end position
    while transport.getSongPos(2) < end_pos and transport.isPlaying():
        # Small delay to avoid busy-waiting
        time.sleep(0.01)
    
    # Send note-off events
    channels.midiNoteOn(channel, 60, 0)  # C off
    channels.midiNoteOn(channel, 64, 0)  # E off
    channels.midiNoteOn(channel, 67, 0)  # G off
    
    # Stop playback and recording
    transport.stop()
    transport.setSongPos(0, 2)
    
    # Exit recording mode
    if transport.isRecording():
        transport.record()
    
    print(f"C major chord recorded to piano roll, length: {length_beats} beats")

def add_hardcoded_melody():
    """Add a predefined melody to the currently selected channel's piano roll"""
    # Get the currently selected channel
    channel = channels.selectedChannel()
    
    if channel < 0:
        print("No channel selected. Please select a channel first.")
        return
    
    # Get the project's PPQ (pulses per quarter note)
    ppq = general.getRecPPQ()
    print(f"Using PPQ value: {ppq}")
    
    # Define the melody as a sequence of [note, position_beats, length_beats]
    # This is a simple C major ascending scale with quarter notes
    melody = [
        [60, 0.00, 0.5],  # C4, beat 1, quarter note
        [62, 0.50, 0.5],  # D4, beat 1.5, quarter note
        [64, 1.00, 0.5],  # E4, beat 2, quarter note
        [65, 1.50, 0.5],  # F4, beat 2.5, quarter note
        [67, 2.00, 0.5],  # G4, beat 3, quarter note
        [69, 2.50, 0.5],  # A4, beat 3.5, quarter note
        [71, 3.00, 0.5],  # B4, beat 4, quarter note
        [72, 3.50, 0.5],  # C5, beat 4.5, quarter note
        [72, 4.00, 1.0],  # C5, beat 5, half note
        [71, 5.00, 0.5],  # B4, beat 6, quarter note
        [69, 5.50, 0.5],  # A4, beat 6.5, quarter note
        [67, 6.00, 0.5],  # G4, beat 7, quarter note
        [65, 6.50, 0.5],  # F4, beat 7.5, quarter note
        [64, 7.00, 0.5],  # E4, beat 8, quarter note
        [62, 7.50, 0.5],  # D4, beat 8.5, quarter note
        [60, 8.00, 1.0],  # C4, beat 9, half note
    ]
    
    # Add each note to the piano roll
    print(f"Adding melody to channel {channel}...")
    for note_data in melody:
        note, position, length = note_data
        
        # Convert beats to ticks
        position_ticks = int(position * ppq)
        length_ticks = int(length * ppq)
        
        # Default values
        velocity = 100  # 0-127 range
        pan = 64        # 0-127 range (64 is centered)
        
        # Add the note to the piano roll
        channels.addNote(channel, position_ticks, length_ticks, note, velocity, pan)
        print(f"Added note {note} at position {position} beats (tick {position_ticks}), length {length} beats (tick {length_ticks})")
    
    # Force refresh of the piano roll
    ui.setFocused(midi.widPianoRoll)
    print("Melody added successfully!")

def record_c_major_progression(chord_length_beats=1.0):
    """
    Records a I-IV-V-I chord progression in C major to the piano roll
    using tick-based timing for precise musical timing
    
    Args:
        chord_length_beats (float): Length of each chord in beats (default: 4.0 = whole note)
    """
    # Get the current channel
    channel = channels.selectedChannel()
    
    # Get the project's PPQ (pulses per quarter note)
    ppq = general.getRecPPQ()
    
    # Define the chord progression (C major, F major, G major, C major)
    progression = [
        [60, 64, 67],  # I (C major: C-E-G)
        [65, 69, 72],  # IV (F major: F-A-C)
        [67, 71, 74],  # V (G major: G-B-D)
        [60, 64, 67]   # I (C major: C-E-G)
    ]
    
    # Calculate ticks for note length
    chord_length_ticks = int(chord_length_beats * ppq)
    
    # Stop playback and recording if active
    if transport.isPlaying():
        transport.stop()
    
    # Reset playback position to beginning before recording
    transport.setSongPos(0, 2)  # Set position to 0 ticks
    
    # Enable recording mode if not already active
    if not transport.isRecording():
        transport.record()
    
    print(f"Recording I-IV-V-I chord progression in C major, each chord: {chord_length_beats} beats")
    
    # Start playback - this begins recording
    transport.start()
    
    # For each chord in the progression
    for chord_index, chord in enumerate(progression):
        # Get current position as the chord start position
        chord_start_pos = transport.getSongPos(2)
        chord_end_pos = chord_start_pos + chord_length_ticks
        
        print(f"Playing chord {chord_index + 1} of 4: {chord}")
        
        # Play the chord notes
        for note in chord:
            channels.midiNoteOn(channel, note, 100)
        
        # Wait until we reach the exact end position based on ticks
        last_pos = chord_start_pos
        
        while transport.isPlaying():
            current_pos = transport.getSongPos(2)
            
            # Wait until position changes before checking again
            # This is much more efficient than sleeping
            if current_pos > last_pos:
                last_pos = current_pos
                
                # If we've reached or passed the end position, stop this chord
                if current_pos >= chord_end_pos:
                    break
        
        # Send note-off events at exactly the right tick position
        for note in chord:
            channels.midiNoteOn(channel, note, 0)
        
        print(f"Stopped chord {chord_index + 1} of 4 at tick position {current_pos}")
    
    # Stop playback and recording
    transport.stop()
    
    # Exit recording mode
    if transport.isRecording():
        transport.record()
    
    # Reset playback position to beginning again
    transport.setSongPos(0, 2)
    
    print("I-IV-V-I chord progression recorded to piano roll")


def record_c_major_chord_in_tempo(length_beats=4.0, position_beats=0.0):
    """
    Records a C major chord to the piano roll synced with project tempo
    
    Args:
        length_beats (float): Length of chord in beats (1.0 = quarter note)
        position_beats (float): Position to place chord in beats from start
    """
    # Make sure we're in recording mode and transport is stopped first
    if transport.isPlaying():
        transport.stop()
    
    if not transport.isRecording():
        transport.record()
    
    # Get the current channel
    channel = channels.selectedChannel()
    
    # Get the project's PPQ (pulses per quarter note)
    ppq = general.getRecPPQ()
    transport.setSongPos(0, 2)
    
    # Calculate ticks based on beats
    length_ticks = int(length_beats * ppq)
    position_ticks = int(position_beats * ppq)
    
    # Set playback position if needed
    if position_beats > 0:
        transport.setSongPos(position_ticks, 2)  # 2 = SONGLENGTH_ABSTICKS
    
    print(f"Recording C major chord to channel {channel}, length: {length_beats} beats")
    
    # Start playback - this begins recording
    transport.start()
    
    # Play the chord notes
    channels.midiNoteOn(channel, 60, 100)  # C
    channels.midiNoteOn(channel, 64, 100)  # E
    channels.midiNoteOn(channel, 67, 100)  # G
    
    # We can't use time.sleep() for tempo synchronization
    # Instead, we'll monitor the song position until we reach the end point
    start_pos = transport.getSongPos(2)  # Get current position in ticks
    end_pos = start_pos + length_ticks
    
    # Wait until we reach the end position
    while transport.getSongPos(2) < end_pos: 
        # Small delay to avoid busy-waiting
        time.sleep(0.01)

    print("taKING NOTES OFF")
    
    # Send note-off events
    channels.midiNoteOn(channel, 60, 0)  # C off
    channels.midiNoteOn(channel, 64, 0)  # E off
    channels.midiNoteOn(channel, 67, 0)  # G off
    
    # Stop playback and recording
    transport.stop()
    transport.setSongPos(0, 2)
    
    # Exit recording mode
    if transport.isRecording():
        transport.record()
    
    print(f"C major chord recorded to piano roll, length: {length_beats} beats")
    
def change_tempo_from_notes(note_array):
    """
    Change the tempo in FL Studio based on an array of MIDI notes
    
    This function converts an array of MIDI notes to a single integer value
    and uses that value as the new tempo.
    
    Args:
        note_array (list): A list of MIDI note values (each 0-127)
    """
    # Convert note array to integer
    bpm_value = midi_notes_to_int(note_array)
    
    # Limit to a reasonable BPM range
    if bpm_value < 20:
        bpm_value = 20  # Minimum reasonable tempo
    elif bpm_value > 999:
        bpm_value = 999  # Maximum reasonable tempo
    
    # Change the tempo
    print(f"Changing tempo to {bpm_value} BPM from note array {note_array}")
    change_tempo(bpm_value)
    
    return bpm_value


def process_command(command):
    """Process a command entered in the terminal"""
    cmd_parts = command.strip().split()
    
    if not cmd_parts:
        return
    
    cmd = cmd_parts[0].lower()
    args = cmd_parts[1:]
    
    # Help command
    if cmd == "help":
        show_help()
    
    # Project commands
    elif cmd == "new":
        ui.new()
        print("Created new project")
    elif cmd == "save":
        ui.saveNew()
        print("Project saved")
    elif cmd == "bpm":
        if args:
            try:
                new_tempo = float(args[0])
                transport.setTempo(new_tempo)
                print(f"Tempo set to {new_tempo} BPM")
            except ValueError:
                print("Invalid tempo value")
        else:
            current_tempo = mixer.getTempo()
            print(f"Current tempo: {current_tempo} BPM")
    
    # Transport commands
    elif cmd == "play":
        transport.start()
        print("Playback started")
    elif cmd == "stop":
        transport.stop()
        print("Playback stopped")
    elif cmd == "record":
        transport.record()
        print("Recording started")
    elif cmd == "loop":
        toggle = args[0].lower() if args else "toggle"
        if toggle == "on":
            transport.setLoopMode(1)
            print("Loop mode enabled")
        elif toggle == "off":
            transport.setLoopMode(0)
            print("Loop mode disabled")
        else:
            current = transport.getLoopMode()
            transport.setLoopMode(0 if current else 1)
            print(f"Loop mode {'enabled' if not current else 'disabled'}")
    
    # Pattern commands
    elif cmd == "pattern":
        if not args:
            print(f"Current pattern: {patterns.patternNumber()}")
            return
            
        subcmd = args[0].lower()
        if subcmd == "new":
            new_pattern = patterns.findFirstEmpty()
            patterns.jumpTo(new_pattern)
            print(f"Created and selected pattern {new_pattern}")
        elif subcmd == "select":
            if len(args) > 1:
                try:
                    pattern_num = int(args[1])
                    patterns.jumpTo(pattern_num)
                    print(f"Selected pattern {pattern_num}")
                except ValueError:
                    print("Invalid pattern number")
            else:
                print("Please specify a pattern number")
        elif subcmd == "clone":
            if len(args) > 1:
                try:
                    source_pattern = int(args[1])
                    new_pattern = patterns.findFirstEmpty()
                    patterns.copyPattern(source_pattern, new_pattern)
                    patterns.jumpTo(new_pattern)
                    print(f"Cloned pattern {source_pattern} to {new_pattern}")
                except ValueError:
                    print("Invalid pattern number")
            else:
                source_pattern = patterns.patternNumber()
                new_pattern = patterns.findFirstEmpty()
                patterns.copyPattern(source_pattern, new_pattern)
                patterns.jumpTo(new_pattern)
                print(f"Cloned current pattern to {new_pattern}")
        elif subcmd == "length":
            if len(args) > 1:
                try:
                    beats = int(args[1])
                    patterns.setPatternLength(beats)
                    print(f"Set pattern length to {beats} beats")
                except ValueError:
                    print("Invalid beat count")
            else:
                print(f"Current pattern length: {patterns.getPatternLength()} beats")
        elif subcmd == "refresh":
            # Force refresh the current pattern
            commit_pattern_changes()
            print("Pattern refreshed")
    
    # Channel commands
    elif cmd == "channel":
        if not args:
            print(f"Current channel: {channels.selectedChannel()}")
            return
            
        subcmd = args[0].lower()
        if subcmd == "select":
            if len(args) > 1:
                try:
                    channel_num = int(args[1])
                    channels.selectOneChannel(channel_num)
                    print(f"Selected channel {channel_num}")
                except ValueError:
                    print("Invalid channel number")
            else:
                print("Please specify a channel number")
        elif subcmd == "add":
            if len(args) > 1:
                preset_type = args[1].lower()
                if preset_type == "sampler":
                    new_channel = channels.addChannel(channels.CH_Sampler)
                elif preset_type == "plugin":
                    new_channel = channels.addChannel(channels.CH_Plugin)
                else:
                    new_channel = channels.addChannel()
                print(f"Added new channel {new_channel}")
                channels.selectOneChannel(new_channel)
            else:
                new_channel = channels.addChannel()
                print(f"Added new channel {new_channel}")
                channels.selectOneChannel(new_channel)
        elif subcmd == "name":
            if len(args) > 1:
                name = " ".join(args[1:])
                channel = channels.selectedChannel()
                channels.setChannelName(channel, name)
                print(f"Renamed channel {channel} to '{name}'")
            else:
                channel = channels.selectedChannel()
                name = channels.getChannelName(channel)
                print(f"Channel {channel} name: '{name}'")
    
    # Note commands
    elif cmd == "note":
        if len(args) >= 3:
            try:
                note_name = args[0].upper()
                position = float(args[1])
                length = float(args[2])
                
                # Convert note name to MIDI note number
                note_map = {"C": 60, "D": 62, "E": 64, "F": 65, "G": 67, "A": 69, "B": 71}
                base_note = note_map.get(note_name[0], 60)
                
                # Apply sharp/flat
                if len(note_name) > 1:
                    if note_name[1] == "#":
                        base_note += 1
                    elif note_name[1] == "B":
                        base_note -= 1
                
                # Apply octave
                if len(note_name) > 1 and note_name[-1].isdigit():
                    octave = int(note_name[-1])
                    base_note = (octave * 12) + (base_note % 12)
                
                # Add note
                pattern = patterns.patternNumber()
                channel = channels.selectedChannel()
                velocity = 100  # Default velocity
                
                if len(args) > 3:
                    try:
                        velocity = int(args[3])
                    except ValueError:
                        pass
                
                # Calculate position in PPQ
                ppq = general.getRecPPQ()
                pos_ticks = int(position * ppq)
                length_ticks = int(length * ppq)
                
                # Add the note
                note_index = channels.addNote(channel, pos_ticks, length_ticks, base_note, velocity, 0)
                print(f"Added note {note_name} at position {position}, length {length}, velocity {velocity} with index {note_index}")
                
                # Force pattern refresh
                commit_pattern_changes()
            except ValueError:
                print("Invalid note parameters. Format: note [name] [position] [length] [velocity]")
        else:
            print("Insufficient parameters. Format: note [name] [position] [length] [velocity]")
    
    # Playlist commands
    elif cmd == "playlist":
        if not args:
            print("Please specify a playlist subcommand")
            return
            
        subcmd = args[0].lower()
        if subcmd == "add":
            if len(args) > 1:
                try:
                    pattern_num = int(args[1])
                    position = float(args[2]) if len(args) > 2 else 1
                    track = int(args[3]) if len(args) > 3 else 0
                    
                    # Calculate position in PPQ
                    ppq = general.getRecPPQ()
                    pos_ticks = int(position * ppq * 4)  # Convert bars to ticks
                    
                    playlist.addPattern(pattern_num, pos_ticks, track)
                    playlist.refresh()  # Force playlist to update
                    print(f"Added pattern {pattern_num} at position {position} on track {track}")
                except ValueError:
                    print("Invalid parameters. Format: playlist add [pattern] [position] [track]")
            else:
                print("Please specify a pattern number")
        elif subcmd == "clear":
            playlist.clearPlaylist()
            print("Cleared playlist")
            playlist.refresh()  # Force playlist to update
        elif subcmd == "refresh":
            playlist.refresh()
            print("Playlist refreshed")
    
    # Mixer commands
    elif cmd == "mixer":
        if not args:
            print(f"Current mixer track: {mixer.trackNumber()}")
            return
            
        subcmd = args[0].lower()
        if subcmd == "select":
            if len(args) > 1:
                try:
                    track_num = int(args[1])
                    mixer.setTrackNumber(track_num)
                    print(f"Selected mixer track {track_num}")
                except ValueError:
                    print("Invalid track number")
            else:
                print("Please specify a track number")
        elif subcmd == "volume":
            if len(args) > 1:
                try:
                    volume = float(args[1])  # 0.0 to 1.0
                    track = mixer.trackNumber()
                    mixer.setTrackVolume(track, volume)
                    print(f"Set mixer track {track} volume to {volume}")
                except ValueError:
                    print("Invalid volume value (0.0 to 1.0)")
            else:
                track = mixer.trackNumber()
                volume = mixer.getTrackVolume(track)
                print(f"Mixer track {track} volume: {volume}")
                
    # Command to force UI refresh
    elif cmd == "refresh":
        ui.crDisplayRect()
        playlist.refresh()
        print("UI refreshed")
    
    # Command to save the project
    elif cmd == "save":
        ui.saveNew()
        print("Project saved")
    
    # Quit command
    elif cmd in ["quit", "exit"]:
        print("Exiting terminal interface...")
        global running
        running = False
    
    # Unknown command
    else:
        print(f"Unknown command: {cmd}")
        print("Type 'help' for a list of commands")
    


def show_help():
    """Display help information"""
    help_text = """
FL STUDIO TERMINAL BEAT BUILDER COMMANDS

PROJECT COMMANDS:
  new                  - Create a new project
  save                 - Save the current project
  bpm [tempo]          - Get or set the project tempo
  refresh              - Force UI refresh

TRANSPORT COMMANDS:
  play                 - Start playback
  stop                 - Stop playback
  record               - Start recording
  loop [on|off|toggle] - Control loop mode

PATTERN COMMANDS:
  pattern              - Show current pattern
  pattern new          - Create a new pattern
  pattern select [num] - Select a pattern
  pattern clone [num]  - Clone a pattern
  pattern length [beats] - Set/get pattern length
  pattern refresh      - Force pattern refresh

CHANNEL COMMANDS:
  channel              - Show current channel
  channel select [num] - Select a channel
  channel add [type]   - Add new channel (sampler, plugin)
  channel name [name]  - Set/get channel name

NOTE COMMANDS:
  note [name] [pos] [len] [vel] - Add a note (e.g., note C4 0 1 100)

PLAYLIST COMMANDS:
  playlist add [pat] [pos] [track] - Add pattern to playlist
  playlist clear                   - Clear playlist
  playlist refresh                 - Force playlist refresh

MIXER COMMANDS:
  mixer                - Show current mixer track
  mixer select [num]   - Select a mixer track
  mixer volume [val]   - Set/get mixer track volume

GENERAL COMMANDS:
  help                 - Show this help
  quit/exit            - Exit terminal interface
"""
    print(help_text)

# Start the terminal interface when loaded in FL Studio
# No need to call this explicitly as OnInit will be called by FL Studio
