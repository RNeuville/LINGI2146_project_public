from mote import MoteInterface
import packet_builder as pkt

class Alarm(MoteInterface):

    mote_type_id = 4
    mote_counter = 1

    action_list = [
        "get_type",
        "ack",
        "set_state",
        "set_ringing"
    ]

    def __init__(self, sensor_ipv6, sensor_port):
        self.ipv6 = sensor_ipv6
        self.port = sensor_port
        self.name = "Alarm" + str(self.mote_counter)
        self.state = 0
        self.ringing = 0
        Alarm.sensor_counter = Alarm.mote_counter + 1 

    def get_sensor_type_id(self):
        return Alarm.mote_type_id

    def get_action_list(self):
        return enumerate(Alarm.action_list)

    def get_status(self):
        if self.state:
            print("Alarm state: activated ")
        else:
            print("Alarm state: deactivated")
        
        if self.ringing:
            print("The alarm is ringing. You can stop the ring with the command: motion-action [motion_id] 3 0")
        else:
            print("The alarm is not ringing")


    def apply_action(self, action_id, token = None, data = None):

        #We want to ask the device what type it is
        if action_id == 0:
            return pkt.create(code=action_id)

        #We need to send an ack
        elif action_id == 1:
            return pkt.create(code=action_id, token=token)

        elif action_id == 2:
            #The alarm has been activated/deactivated
            if token is not None:
                self.state = data
            else:
                if data is None:
                    print("Missing payload value, possible value: 0 or 1")
                    return None, None
                else:
                    #We send a message to the alarm the activate/deactivate it
                    self.state = data
                    return pkt.create(code=action_id, ack = 1, payload = data)

        elif action_id == 3:
            #The alarm is/stop ringing
            if token is not None:
                self.ringing = data
                self.state = 1

                if data:
                    print("THE ALARM IS RINGING !")

            else:
                if data is None:
                    print("Missing payload value, possible value: 0 or 1")
                    return None, None, None

                #The alarm needs to be activated before ringing
                elif self.state == 0:
                    print("To ring the alarm, you have to activate it first with the command:")
                    print("mote-action [mote_id] 2 1")

                #We send a message to make the alarm ring or to stop the ringing
                else:
                    self.ringing = data
                    return pkt.create(code=action_id, ack = 1, payload = data)

        else:
            print("Unknown action_id for " + self.name)
            return None, None, None

    
