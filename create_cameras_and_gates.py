from camera_creator import CameraCreator
from gate_creator import GateCreator

camera_creator = CameraCreator()
server_name = camera_creator.create_cameras_json()

gate_creator = GateCreator()
gate_creator.create_gates_json(server_name)