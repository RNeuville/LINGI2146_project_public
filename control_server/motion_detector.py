from mote import MoteInterface
import packet_builder as pkt
from datetime import datetime

class MotionDetector(MoteInterface):

    mote_type_id = 3
    mote_counter = 1

    action_list = [
        "get_type",
        "ack",
        "latest_detection"
    ]

    def __init__(self, sensor_ipv6, sensor_port):
        self.ipv6 = sensor_ipv6
        self.port = sensor_port
        self.name = "MotionDetector" + str(self.mote_counter)
        self.latest_detection = "No detection"
        MotionDetector.sensor_counter = MotionDetector.mote_counter + 1 

    def get_sensor_type_id(self):
        return MotionDetector.mote_type_id

    def get_action_list(self):
        return enumerate(MotionDetector.action_list)

    def get_status(self):
        print("Latest detection at " + str(self.latest_detection))


    def apply_action(self, action_id, token = None, data = None):

        #We want to ask the device what type it is
        if action_id == 0:
            return pkt.create(code=action_id)

        #We need to send an ack
        elif action_id == 1:
            return pkt.create(code=action_id, token=token)

        elif action_id == 2:
            #We have received a detection message from the motion detector
            if token is not None:
                now = datetime.now()
                self.latest_detection = now.strftime("%H:%M:%S %d/%m/%Y")
            else:
                print("To know the latest_detection, type mote-status [motion_id] with the motion_id of the detector")
                return None, None, None

        else:
            print("Unknown action_id for " + self.name)
            return None, None, None