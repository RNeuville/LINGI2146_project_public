import sys
import socket
import select
import struct
import time
import packet_builder as pkt
import temperature_sensor
import humidity_sensor
import motion_detector
import alarm

running = 1
mote_list = []
mote_ipv6 = {}
ack_waiting_token = []
ack_waiting_info = {}


#Function used to handle to user input from the command line interface
def handle_user_input(command):

    parsed_command = command.split()
    print("")

    if parsed_command[0] == "help":
        if len(parsed_command)  != 1:
            print("help command doesn't take any argument")
        
        else:
            print("Here is the list of available commands:")
            print("")
            print("exit : stop the control server")
            print("")
            print("mote-list : show the list of motes and their corresponding mote_id")
            print("")
            print("mote-action-list [mote_id] :  show a list of actions and their corresponding action_id that can be performed on the mote corresponding to mote_id ")
            print("")
            print("mote-action [mote_id] [action_id] ([payload_data]) : perform the action corresponding to the action_id for the mote corresponding to mote_id")
            print("payload_data is optionnal and must be an integer between 0 and 255")
            print("")
            print("mote-status [mote_id] : show status information about the mote corresponfing to mote_id")

        return 1, None, None, None

    if parsed_command[0] == "exit":
        if len(parsed_command)  != 1:
            print("exit command doesn't take any argument")
            return 1, None, None, None

        else:
            print("Stopping control server")
            return 0, None, None, None

    elif parsed_command[0] == "mote-list":
        if len(parsed_command)  != 1:
            print("mote-list command doesn't take any argument")
        
        else:
            for id, mote in enumerate(mote_list):
                print("mote_id: " + str(id) + " -> " + mote.name)
                print("")
        return 1, None, None, None

    elif parsed_command[0] == "mote-action-list":
        if len(parsed_command) != 2:
            print("Incorrect usage, mote-action-list usage: mote-action-list [mote_id]")
        else:
            for id, action in mote_list[int(parsed_command[1])].get_action_list():
                print("action_id: " + str(id) + "; action: " + action)
        return 1, None, None, None

    elif parsed_command[0] == "mote-action":
        if len(parsed_command) < 3:
            print("Missing argument, mote-actions usage: mote-actions [mote_id] [action_id] ([payload_data])")
            return 1, None, None, None

        elif len(parsed_command) == 3:
            data, token, ack = mote_list[int(parsed_command[1])].apply_action(int(parsed_command[2]))
            return 2, data, token, ack

        elif len(parsed_command) == 4:
            data, token, ack = mote_list[int(parsed_command[1])].apply_action(int(parsed_command[2]), data = int(parsed_command[3]))
            return 2, data, token, ack

        else:
            print("Too many arguments, mote-actions usage: mote-actions [mote_id] [action_id] ([payload_data])")
            return 1, None, None, None

    elif parsed_command[0] == "mote-status":
        if len(parsed_command) != 2:
            print("Incorrect usage, mote-status usage: mote-status [mote_id]")

        else:
            mote_list[int(parsed_command[1])].get_status()
        return 1, None, None, None

    else:
        print("Unknown command")
        return 1, None, None, None


if len(sys.argv) != 3:
    print("The control server requires 2 arguments to starts:")
    print("1st argument: ipv6 address of the server")
    print("2nd argument: the port that will be used to send the control messages to the iot devices")
    print("")
    sys.exit()


#Getting the ipv6 address and the port that will be used by the control server
SERVER_IP = sys.argv[1]
SERVER_PORT = int(sys.argv[2])

#Setting the port on which the mote are listening
MOTE_PORT = 8765

#Creating the socket of the server
serverSocket = socket.socket(family=socket.AF_INET6, type=socket.SOCK_DGRAM)
serverSocket.bind((SERVER_IP, SERVER_PORT))


#################################################################
#Registering the mote with their ipv6 address, edit if necessary#
#################################################################
temperature_mote = temperature_sensor.TemperatureSensor("bbbb::c30c:0:0:1", MOTE_PORT)
mote_list.append(temperature_mote)
mote_ipv6[temperature_mote.ipv6] = mote_list.index(temperature_mote)

humidity_mote = humidity_sensor.HumiditySensor("bbbb::c30c:0:0:2", MOTE_PORT)
mote_list.append(humidity_mote)
mote_ipv6[humidity_mote.ipv6] = mote_list.index(humidity_mote)

detection_mote = motion_detector.MotionDetector("bbbb::c30c:0:0:3", MOTE_PORT)
mote_list.append(detection_mote)
mote_ipv6[detection_mote.ipv6] = mote_list.index(detection_mote)

alarm_mote = alarm.Alarm("bbbb::c30c:0:0:4", MOTE_PORT)
mote_list.append(alarm_mote)
mote_ipv6[alarm_mote.ipv6] = mote_list.index(alarm_mote)
###############################################################


readable_socket_list = [sys.stdin, serverSocket]
timeout = 30
ack_timeout = 60

#Starting the main loop
print("To get a list of available command, type help")
while(running):
    print("----------------------------------------")
    print("Waiting for a command or incoming packet:")

    #Waiting for a user input or a packet on the socket of the server
    #If there are packets waiting for ack, we only for [timeout] seconds
    if len(ack_waiting_token) == 0:
        read_sockets, write_sockets, error_sockets = select.select(readable_socket_list , [], [])
    else:
        read_sockets, write_sockets, error_sockets = select.select(readable_socket_list , [], [], timeout)

    for sock in read_sockets:

        #If we received a packet on the socket
        if sock == serverSocket:
            print("")
            data, addr = serverSocket.recvfrom(3)

            #We check who sent the packet
            if addr[0] not in mote_ipv6:
                print("Incoming packet from an unknown mote, ignoring")
                print(addr[0])
            else:
                sender = mote_list[mote_ipv6[addr[0]]]
                print("Incoming packet from " + sender.name)

                content = pkt.decode(data[:2])
                print("Action_id: " + str(content["action_id"]))

                #If it is an ack, we remove it from the ack_waiting_token list if the corresponding token matches with an element of the list
                if content["action_id"] == 1:
                    if content["token"] in ack_waiting_token:
                        ack_waiting_token.remove(content["token"])
                        ack_waiting_info[content["token"]] == None

                    else:
                        print("Unexpected ack, ignoring")
                
                else:
                    #If the packet asks for an ack, we send it
                    if content["ack_flag"]:
                        print("Sending ack packet to " + sender.name)
                        to_send, _, _ = sender.apply_action(1, token = content["token"])
                        serverSocket.sendto(to_send, (addr[0], addr[1]))

                    #If the packet has a payload, we decode it
                    #And then we perform the action corresponding to the code (and the payload)
                    if content["has_payload"]:
                        content["payload"] = struct.unpack('>B', data[2])[0]
                        sender.apply_action(content["action_id"], token = content["token"], data = content["payload"])
                    
                    else:
                        sender.apply_action(content["action_id"], token = content["token"])

        #We have an input command from the user
        else:
            command = sys.stdin.readline()
            parsed_command = command.split()
            running, data, token, ack = handle_user_input(command)

            #If the command asks to send a particular messages to a device, we send it.
            #And if this messages needs to be acked, we ad its token to the ack_waiting_token list and we keep the message data.
            if running == 2 and data != None:
                serverSocket.sendto(data, (mote_list[int(parsed_command[1])].ipv6, MOTE_PORT))
                running = 1
            
                if ack:
                    current_time = time.time()
                    ack_waiting_token.append(token)
                    ack_waiting_info[token] = (current_time, data, mote_list[int(parsed_command[1])].ipv6)
                    running = 1

    #We check if a packet needs to be sent again
    if len(ack_waiting_token) != 0:
        for token in ack_waiting_token:
            current_time = time.time()
            to_resend = ack_waiting_info[token]
            
            if(current_time - to_resend[0] > ack_timeout):     
                print("Resending a packet")
                serverSocket.sendto(to_resend[1], (to_resend[2], MOTE_PORT))
                ack_waiting_info[token] = (current_time, to_resend[1], to_resend[2])
