#!/usr/bin/env python
import rospy
import json

from std_msgs.msg import String
from .polip_device_v1.polip_device import PolipDevice
from .polip_device_v1.constants import POLIP_DEFAULT_POLL_STATE_PERIOD

from polip_device.msg import PolipError
from polip_device.srv import PolipDeviceSchema, PolipDeviceSchemaResponse
from polip_device.srv import PolipErrorSemantic, PolipErrorSemanticResponse
from polip_device.srv import PolipErrorSemanticCode, PolipErrorSemanticCodeResponse


class PolipDeviceRosDriver:
    def __init__(self, polip_device):
        self.polip_device = polip_device
        self.state_pub = rospy.Publisher("polip_device/state", String, queue_size=10)
        
        self.sensors_sub = rospy.Subscriber("polip_device/sensors", String, self.sensors_callback)
        self.error_sub = rospy.Subscriber("polip_device/error", PolipError, self.error_callback)
        self.rpc_sub = rospy.Subscriber("polip_device/rpc_result", String, self.rpc_callback)
        
        self.schema_srv = rospy.Service('polip_device/schema', PolipDeviceSchema, self.schema_request)
        self.all_error_semantic_srv = rospy.Service('polip_device/error_semantic', PolipErrorSemantic, self.all_error_semantic_request)
        self.error_semantic_srv = rospy.Service('polip_device/error_semantic/code', PolipErrorSemanticCode, self.error_semantic_request)

    def publish_state(self):
        state = self.polip_device.get_state()
        self.state_pub.publish(String(data=json.dumps(state)))

    def sensors_callback(self, msg):
        sensors_data = json.loads(msg.data)  # Convert string back to dictionary
        self.polip_device.push_sensors(sensors_data)

    def error_callback(self, msg):
        self.polip_device.push_error(msg.message, msg.code)

    def rpc_callback(self, msg):
        rpc_data = json.loads(msg.data)  # Convert string back to dictionary
        self.polip_device.push_rpc(rpc_data)

    def schema_request(self, _):
        schema = self.polip_device.get_schema()
        return PolipDeviceSchemaResponse(schema=json.dumps(schema))
    
    def all_error_semantic_request(self, req):
        semantic = self.polip_device.get_error_semantic()
        return PolipErrorSemanticResponse(semantic=json.dumps(semantic))

    def error_semantic_request(self, req):
        semantic = self.polip_device.get_error_semantic(req.code)
        return PolipErrorSemanticCodeResponse(semantic=json.dumps(semantic))


if __name__ == "__main__":
    rospy.init_node("polip_device_ros_driver", anonymous=True)

    # Create an instance of your PolipDevice with the required parameters
    polip_device = PolipDevice()

    # Create an instance of the PolipDeviceRosDriver
    polip_device_ros_driver = PolipDeviceRosDriver(polip_device)

    rate = rospy.Rate(POLIP_DEFAULT_POLL_STATE_PERIOD)  # 1 Hz

    while not rospy.is_shutdown():
        polip_device_ros_driver.publish_state()
        rate.sleep()