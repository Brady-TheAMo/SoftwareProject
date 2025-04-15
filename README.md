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
2. Start the traffic generator by entering `python3 trafficGenerator.py`. T

   -Follow the instructions on the terminal by entering the hardware ID for each player.
3. In a separate terminal go to the same directory you downloaded/installed the files to and enter `python3 main.py` to start the application.
