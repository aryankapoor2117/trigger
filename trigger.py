from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import mido
import time

# Initialize FastMCP server
mcp = FastMCP("weather")
output_port = mido.open_output('loopMIDI Port 2') 

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

@mcp.tool()
def record():
    """Send MIDI message to start recording in FL Studio"""
    # Send Note On for D3 (note 62)
    output_port.send(mido.Message('note_on', note=62, velocity=100))
    time.sleep(0.1)  # Small delay
    output_port.send(mido.Message('note_off', note=62, velocity=0))
    print("Sent Record command")

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')