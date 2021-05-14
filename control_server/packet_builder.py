from random import randrange
import struct

IS_FLAG = {0,1}

#Returns the byte array corresponding to the code, ack, token and payload
#If the token is not given in the call, generates one
def create(code, ack=0, token=None, payload=None):
    if token == None:
        token = generate_token()

    bit_code = "{0:04b}".format(code)

    ack_flag = str(0)
    if ack not in IS_FLAG:
        print("Warning: ack must be 0 or 1, setting it to 0")
    else:
        ack_flag = str(ack)

    has_payload_flag = str(0)
    
    bit_payload = ""
    if payload is not None:
        has_payload_flag = str(1)
        bit_payload = "{0:08b}".format(payload)

    if token == None:
        token = generate_token()
    
    bit_sequence = bit_code + ack_flag + has_payload_flag + token + bit_payload
    split_sequence = ['0b' + bit_sequence[i:i+8] for i in range(0, len(bit_sequence), 8)]
    bytes_sequence = [int(i, 2) for i in split_sequence]

    return bytearray(bytes_sequence), token, ack


#Used to decode the first 2 bytes of a received message
#Returns a dictionnary containing the code, the ack_flag, the has_payload flag and the token
def decode(data):
    content = {}
    unpacked = struct.unpack('>BB', data)
    bit_sequence = ["{0:08b}".format(val) for val in unpacked]

    content["action_id"] = int(bit_sequence[0][:4], 2)
    content["ack_flag"] = int(bit_sequence[0][4])
    content["has_payload"] = int(bit_sequence[0][5])
    content["token"] = bit_sequence[0][6:] + bit_sequence[1]
    return content

#Generate a token
def generate_token():
    retval = ''
    for i in range(10):
        retval += str(randrange(2))
    return str(retval)
