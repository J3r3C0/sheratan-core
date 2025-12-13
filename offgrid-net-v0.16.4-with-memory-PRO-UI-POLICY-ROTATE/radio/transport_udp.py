#!/usr/bin/env python3
import socket, struct

class UdpMulticast:
    def __init__(self, group="239.23.0.7", port=47007, iface="0.0.0.0", ttl=1):
        self.group = group; self.port = port
        self.tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.tx.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        self.rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.rx.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.rx.bind(("", port))
        except OSError:
            self.rx.bind((group, port))
        mreq = struct.pack("=4sl", socket.inet_aton(group), socket.INADDR_ANY)
        self.rx.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self.rx.settimeout(1.0)

    def send(self, frame: bytes):
        self.tx.sendto(frame, (self.group, self.port))

    def recv(self, timeout_s: float = 1.0) -> bytes:
        self.rx.settimeout(timeout_s)
        try:
            data, _ = self.rx.recvfrom(2048)
            return data
        except Exception:
            return b""

    def close(self):
        try:
            self.tx.close()
        finally:
            try:
                self.rx.close()
            except:
                pass
