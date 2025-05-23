hex_str = "2424443134322C3836353431333035363937333233322C4343452C0000000001006C0014000601010501060A071A1501FE6960050803000931000A08000B75061A770007024EF83A0103A9CAD5F90475DCC02F0C543507000D871A0E001C41000000FE3759000000020E0C4E0114001A14022C350200004B16010113464444204C5445284C54452042414E442034292A32420D0A"

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

    return {
        "latitude": latitude,
        "longitude": longitude
    }

def parse_custom_coord(hex_str):
    # Ensure we have 4 bytes (8 hex chars)
    if len(hex_str) != 8:
        raise ValueError("Expected 4 bytes (8 hex chars)")

    # Convert hex to bytes, assuming it's in big-endian order (v4 v3 v2 v1)
    bytes_val = bytes.fromhex(hex_str)
    if len(bytes_val) != 4:
        raise ValueError("Hex input must convert to 4 bytes")

    v1, v2, v3, v4 = bytes_val  # unpack bytes

    # Combine into 32-bit unsigned int
    combined = (v4 << 24) | (v3 << 16) | (v2 << 8) | v1

    # Convert to float coordinate
    value = combined / 30000.0

    # Extract degrees and decimal minutes
    degrees = int(value / 60)
    minutes = value - (degrees * 60)

    # Final float representation (e.g., 22.5460833)
    decimal_degrees = degrees + (minutes / 60)

    return decimal_degrees

gps_data = parse_gps_frame(hex_str)
print(f"Latitude: {gps_data['latitude']}, Longitude: {gps_data['longitude']}")
print(f"Custom Coordinate: {parse_little_endian_coord('25875701')}")