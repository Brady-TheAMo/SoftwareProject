import socket
import sys

def send_message(target_ip, message, port=7501):
    """Send a UDP message to the target IP on the specified port."""
    # Create UDP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Enable broadcast if target IP is the broadcast address
    if target_ip == "255.255.255.255":
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # Convert the message to bytes and send it
    bytes_to_send = str.encode(message)
    client_socket.sendto(bytes_to_send, (target_ip, port))
    print(f"Sent message '{message}' to {target_ip}:{port}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python udp_client.py <target_ip> <message>")
        sys.exit(1)

    target_ip = sys.argv[1]
    message = sys.argv[2]
    send_message(target_ip, message)

if __name__ == "__main__":
    main()
