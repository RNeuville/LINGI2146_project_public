from mote import MoteInterface
import packet_builder as pkt

class HumiditySensor(MoteInterface):

    mote_type_id = 2
    mote_counter = 1

    action_list = [
        "get_type",
        "ack",
        "get_humidity"
    ]

    def __init__(self, sensor_ipv6, sensor_port):
        self.ipv6 = sensor_ipv6
        self.port = sensor_port
        self.name = "HumiditySensor" + str(self.mote_counter)
        self.humidity = None
        HumiditySensor.sensor_counter = HumiditySensor.mote_counter + 1 

    def get_sensor_type_id(self):
        return HumiditySensor.mote_type_id

    def get_action_list(self):
        return enumerate(HumiditySensor.action_list)

    def get_status(self):
        print("Latest known humidity value is " + str(self.humidity))


    def apply_action(self, action_id, token = None, data = None):

        #We want to ask the device what type it is
        if action_id == 0:
            return pkt.create(code=action_id)

        #We need to send an ack
        elif action_id == 1:
            return pkt.create(code=action_id, token=token)


        elif action_id == 2:

            #We have received a humidity value
            if token is not None:
                self.humidity = data

            #We want to ask the current humidity value to the humidity sensor
            else:
                return pkt.create(code=action_id)

        else:
            print("Unknown action_id for " + self.name)
            return None, None, None