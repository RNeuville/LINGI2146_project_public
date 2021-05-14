class MoteInterface:

#Interface containing the fonction that the python class representing an IoT device has to implement

    #Returns the type_id corresponding to the type of the IoT device.
    #Each device type has a unique type_id that identifies the type of the device.
    def get_sensor_type_id(self):
        pass

    #Returns an enumeration of the actions that can be performed on the deviceand their corresponding action id.
    def get_action_list(self):
        pass

    #Prints information describing the status of the device
    def get_status(self):
        pass

    #Contains the logic corresponding to the actions in the action list of each device 
    #and also the logic to interpret received messages from the device
    def apply_action(self, action_id, token, data):
        pass

    