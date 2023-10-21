import socket
import select
import sys
import time
import errno
import pandas as pd

HEADER_LENGTH = 10

IP = "127.0.0.1"
PORT = 1234
my_username = input("Username: ")

# Read sensor data from an Excel file (assuming data.xlsx is your file)
data_file = "data.xlsx"
sensor_data = pd.read_excel(data_file)

# Create a socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((IP, PORT))
client_socket.setblocking(False)

# Prepare username and header and send them
username = my_username.encode('utf-8')
username_header = f"{len(username):<{HEADER_LENGTH}}".encode('utf-8')
client_socket.send(username_header + username)

# Create a dictionary to keep track of the last message sent and its timestamp
last_message_sent = {}
timeout = 3  # Set your desired timeout value in seconds


# Iterate through sensor data
for index, row in sensor_data.iterrows():
    timestamp = row["Timestamp"]
    rotation_count = row["Wheel Rotation Count"]

    message = f"{timestamp}, {rotation_count}"
    message = message.encode('utf-8')
    message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
    client_socket.send(message_header + message)

    # Timestamp the message
    timestamp = time.time()
    print(f'Sent: {message.decode("utf-8")}')

    # Save the last sent message and its timestamp
    last_message_sent[message] = timestamp

while True:
    try:
        while True:
            # Receive ACK message
            ack_header = client_socket.recv(HEADER_LENGTH)
            if not ack_header:
                print('Connection closed by the server')
                sys.exit()
            ack_length = int(ack_header.decode('utf-8').strip())
            ack = client_socket.recv(ack_length).decode('utf-8')

            # If we receive an ACK, remove the corresponding message from last_message_sent
            messages_to_delete = []
            for message, timestamp in last_message_sent.items():
                if message.decode('utf-8') in ack:
                    rtt = time.time() - timestamp
                    print(f'RTT for message {message.decode("utf-8")}: {rtt:.3f} seconds')
                    messages_to_delete.append(message)

            # Remove the processed messages from the dictionary
            for message in messages_to_delete:
                del last_message_sent[message]


    except BlockingIOError as e:
        # Handle non-blocking socket operation error
        pass

    except IOError as e:
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print('Reading error: {}'.format(str(e)))
            sys.exit()

    except Exception as e:
        print('Reading error: '.format(str(e)))
        sys.exit()