import socket
import threading
from datetime import datetime
from flask import Flask, render_template
import folium
import os
import time

latest_position = {
    "latitude": 0,
    "longitude": 0,
    "event": "Waiting...",
    "datetime": "Never",
    "battery": 0,
}

event_dict = {
    1: "SOS Pressed",
    17: "Low Battery",
    19: "Speeding",
    20: "Enter Geo-fence",
    21: "Exit Geo-fence",
    24: "GPS Signal Lost",
    25: "GPS Signal Recovery",
    26: "Enter Sleep",
    27: "Exit Sleep",
    29: "Device Reboot",
    31: "Heartbeat",
    32: "Cornering",
    33: "Track By Distance",
    34: "Reply Current (Passive)",
    35: "Track By Time Interval",
    36: "Tow",
    40: "Power Off",
    70: "Reject Incoming Call",
    72: "Auto Answer Incoming Call",
    73: "Listen-in (Voice Monitoring)",
    79: "Fall",
    111: "Call Record",
    127: "Alarm Clock Info",
    152: "Start Trip",
    153: "End Trip",
    154: "Reset Step",
    155: "Within Frequent Parking Place",
    156: "Outside Frequent Parking Place",
    157: "Lost",
    158: "Lost Recovery"
}

def get_bytes(hex_str, start_byte, num_bytes):
    return hex_str[start_byte * 2 : (start_byte + num_bytes) * 2]

def parse_little_endian_coord(hex_str):
    # Take the last 4 bytes (8 hex chars), reverse for little endian
    hex_val = hex_str[-8:]
    bytes_le = bytes.fromhex(hex_val)
    int_val = int.from_bytes(bytes_le, byteorder='little', signed=True)
    return int_val / 1000000

def parse_gps_frame(hex_str):
    parsed = {
    "header":                get_bytes(hex_str, 0, 27),  # up to before "00000000"
    "remaining_cache":       get_bytes(hex_str, 27, 4),
    "packet_count":          get_bytes(hex_str, 31, 2),
    "data_length":           get_bytes(hex_str, 33, 2),
    "total_id_count":        get_bytes(hex_str, 35, 2),
    "param_id_count":        get_bytes(hex_str, 37, 1),
    "event_code":            get_bytes(hex_str, 38, 2),
    "gps_status":            get_bytes(hex_str, 40, 2),
    "num_sats":              get_bytes(hex_str, 42, 2),
    "gsm_signal":            get_bytes(hex_str, 44, 2),
    "input_port_status":     get_bytes(hex_str, 46, 2),
    "battery":               get_bytes(hex_str, 48, 3),
    "reserved1":             get_bytes(hex_str, 51, 1),
    "speed":                 get_bytes(hex_str, 52, 3),
    "direction":             get_bytes(hex_str, 55, 3),
    "hdop":                  get_bytes(hex_str, 58, 3),
    "altitude":              get_bytes(hex_str, 61, 3),
    "ad5":                   get_bytes(hex_str, 64, 3),
    "reserved2":             get_bytes(hex_str, 67, 1),
    "latitude":              get_bytes(hex_str, 68, 5),
    "longitude":             get_bytes(hex_str, 73, 5),
    "datetime":              get_bytes(hex_str, 78, 5),
    "mileage":               get_bytes(hex_str, 83, 5),
    "run_time":              get_bytes(hex_str, 88, 5),
    "system_flag":           get_bytes(hex_str, 93, 5),
    "steps":                 get_bytes(hex_str, 98, 6),
    "remaining_data":        hex_str[104 * 2:]  # everything after byte 116
    }
    # Extract the latitude and longitude from the parsed data
    latitude_hex = parsed["latitude"]
    longitude_hex = parsed["longitude"]

    # Convert hex to little-endian coordinates
    latitude = parse_little_endian_coord(latitude_hex)
    longitude = parse_little_endian_coord(longitude_hex)
    event = int(str(parsed["event_code"])[2:], 16)
    battery = int(str(parsed["battery"])[4:], 16)

    return {
        "latitude": latitude,
        "longitude": longitude,
        "event": event_dict.get(event, "Unknown Event"),
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "battery": f'{battery}%',
    }

def tcp_server(host='0.0.0.0', port=5000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"[TCP Server] Listening on {host}:{port}...")
        while True:
            conn, addr = s.accept()
            print(f"[TCP Server] Connected by {addr}")
            with conn:
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    raw_hex = data.hex()
                    parsed = parse_gps_frame(raw_hex)
                    if parsed:
                        print(f"[Parsed] {parsed}")
                        latest_position.update(parsed)

app = Flask(__name__)

@app.route("/")
def index():
    lat = latest_position["latitude"]
    lon = latest_position["longitude"]
    label = f"{latest_position['event']} at {latest_position['datetime']}\nBattery: {latest_position['battery']}"

    m = folium.Map(location=[lat, lon], zoom_start=16)
    folium.Marker([lat, lon], tooltip=label).add_to(m)

    # Save to static folder (not templates)
    map_path = os.path.join("static", "map.html")
    m.save(map_path)

    # Pass a timestamp to force iframe reload
    return render_template("index.html", label=label, timestamp=int(time.time()))

# ------------------ START EVERYTHING ------------------

if __name__ == "__main__":
    # Start TCP server in a background thread
    threading.Thread(target=tcp_server, daemon=True).start()

    # Run Flask app
    app.run(host="0.0.0.0", port=8000)
    