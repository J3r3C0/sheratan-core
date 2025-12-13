#!/usr/bin/env python3
import base64, sys
if __name__ == "__main__":
    if len(sys.argv)<2:
        print("Usage: python radio/ble_name_encode.py <endpoint>"); sys.exit(1)
    ep = sys.argv[1]
    enc = base64.urlsafe_b64encode(ep.encode()).decode().rstrip("=")
    print("OFFGRID:" + enc)
