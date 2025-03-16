# Phaser Laser Tag System

## Team Members
- Brady Morgan - https://github.com/Brady-TheAMo

- Eli Young - https://github.com/eliyoung1

- Kolby Stoll - https://github.com/KolbyStoll

- Matthew Andrews - https://github.com/Matthew-C-Andrews

## Overview

This project is the main software for a laser tag system designed to run on a Debian Virtual Machine. The application is written in Python and uses:
- **Pygame** for the graphical user interface,
- **Psycopg2** for PostgreSQL database connectivity
- **UDP sockets** for communication between system components.

The application displays a splash screen on startup, then transitions into an entry screen where players can be added or updated. Equipment IDs are broadcast via UDP, and a separate UDP server is available to receive incoming messages.

## Requirements
- Python

- Pygame

- Psycopg2

- PostgreSQL

## How to Install Dependencies

** On the Debian Virtual Machine that already has PostgreSQL, open a terminal. **
1. Install Python 3 and Pip:
   
   `sudo apt-get install python3-pip`
   
    Verify with
   
   `python3 --version`
   
   `pip3 --version`
2. Install Pygame:

   `pip3 install pygame`
3. Install Psycopg2:
   
   `pip3 install psycopg2-binary`

## How to Run
1. Download zip file and extract it. On the terminal, go to the directory where you extracted the file to. 
2. Start the server by entering `python3 udp_server.py`. This defaults to 0.0.0.0 to listen on all interfaces on port 7501.

   -Only testing functionality right now with udp_client or changing port in main.py since no player gameplay has been created yet.

   -To start the server on a specific IP and Port enter `python3 udp_server.py 127.0.0.1 7501` or whatever IP and Port you choose. The IP address still has to be assigned to your machine.
3. In a separate terminal go to the same directory you downloaded/installed the files to and enter `python3 main.py` to start the application.

## Testing UDP Server
1. Download `udp_server.py` and `udp_client.py`
2. In the terminal go to the install directory and run `python3 udp_server.py`

   -This will start the UDP server listening on all local interfaces on port 7501
   
   -For manual IP and Port use, refer to the How to Run section
4. In a separate terminal go to the install directory and run `python3 udp_client.py 127.0.0.1 "Test Message"` as an example.

The Client sends on Port 7501 and the Server recieves on port 7501. The Server listens on all local interfaces. The Client requires an IP address and message as arguments.
