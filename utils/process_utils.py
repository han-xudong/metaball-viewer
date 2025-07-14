#!/usr/bin/env python3

"""
Utility functions for processing in the Metaball Viewer.
"""

import os
import time
import trimesh
import numpy as np
import matplotlib.pyplot as plt
import rerun as rr
from multiprocessing import Queue, Value
from scipy.spatial.transform import Rotation as R
from modules.zmq import MetaballSubscriber
from .log_utils import log_camera, log_metaball, log_state_dict, log_asset
from .data_utils import parse_data


class MetaballVis:
    def __init__(self) -> None:
        """
        Initialize the MetaballVis class.
        """

        # Initialize time tracking for logging
        self.log_time = 0.0

        # Initialize the metaball mesh
        assets_dir = os.path.join("assets")
        metaball_mesh_dir = os.path.join(assets_dir, "metaball")
        if not os.path.exists(metaball_mesh_dir):
            raise FileNotFoundError(f"Assets directory {metaball_mesh_dir} does not exist.")
        # Load the metaball mesh from files
        surf_coor_path = os.path.join(metaball_mesh_dir, "surface_coordinate.txt")
        metaball_vertices = np.loadtxt(surf_coor_path, delimiter=",")
        surf_tri_path = os.path.join(metaball_mesh_dir, "surface_triangle.txt")
        metaball_faces = np.loadtxt(surf_tri_path, delimiter=",").astype(int) - 1
        self.metaball_mesh = trimesh.Trimesh(
            vertices=metaball_vertices, faces=metaball_faces
        )
        self.metaball_node_num = len(self.metaball_mesh.vertices)
        self.metaball_def_node = np.loadtxt(
            os.path.join(metaball_mesh_dir, "deform_node.txt"), dtype=int
        )
        self.metaball_colormap = [plt.get_cmap("viridis")(i / 255) for i in range(256)]
        self.metaball_cmin = 0.0
        self.metaball_cmax = 10.0
        
        # Log the metaball base
        metaball_base_dir = os.path.join(assets_dir, "metaball_base")
        if not os.path.exists(metaball_base_dir):
            raise FileNotFoundError(f"Assets directory {metaball_base_dir} does not exist.")
        log_asset(
            log_path="metaball_base", 
            file_path=os.path.join(metaball_base_dir, "metaball_base.obj"),
            translation=np.array([0, 0, -30]),
            mat3x3=np.array([
                [-1, 0, 0],
                [0, 0, 1],
                [0, 1, 0],
            ]),
            scale=10.0,
        )

        # Log the metaball mesh
        log_metaball(
            "metaball",
            np.zeros([len(self.metaball_def_node), 3]),
            self.metaball_mesh,
            self.metaball_node_num,
            self.metaball_def_node,
            self.metaball_colormap,
            self.metaball_cmin,
            self.metaball_cmax,
        )

    def run(
        self,
        zmq_queue: Queue,
        recording_queue: Queue,
        is_recording,
        start_time,
    ) -> None:
        """
        Run the viewer in live mode.

        Args:
            zmq_queue (Queue): The queue for receiving the data.
            recording_queue (Queue): The queue for recording the data.
            is_recording (Value): A multiprocessing Value indicating whether recording is active.
            start_time (Value): A multiprocessing Value to store the start time of the recording.

        Raises:
            KeyboardInterrupt: If Ctrl+C is pressed, the viewer will terminate.
            Exception: If any other error occurs, it will be printed and the viewer will terminate.
        """

        # Run the viewer
        try:
            while True:
                if not zmq_queue.empty():
                    # Receive the data from the queue
                    metaball_data = zmq_queue.get()

                    # Log the metaball mesh
                    metaball_node = metaball_data["node"]
                    log_metaball(
                        "metaball",
                        metaball_node,
                        self.metaball_mesh,
                        self.metaball_node_num,
                        self.metaball_def_node,
                        self.metaball_colormap,
                        self.metaball_cmin,
                        self.metaball_cmax,
                    )

                    # Log the camera images
                    log_camera(
                        imgs={
                            "metaball": np.frombuffer(
                                metaball_data["img"], dtype=np.uint8
                            )
                        }
                    )

                    # Log the state dictionary
                    log_state_dict(
                        state_dict={
                            "metaball/pose": metaball_data["pose"],
                            "metaball/force": metaball_data["force"],
                        }
                    )

                    # Put the data into the recording queue
                    if is_recording.value == 1:
                        recording_queue.put(
                            {
                                "time": time.time() - start_time.value,
                                **metaball_data,
                            }
                        )
        except KeyboardInterrupt:
            print("\nCtrl+C detected. Terminating viewer...")
            return
        except Exception as e:
            print(f"An error occurred: {e}")
            return

    def log(
        self,
        data: dict,
        start_time,
    ) -> None:
        """
        Log the data for the replay mode.

        Args:
            data: The data to be logged.
            start_time (Value): A multiprocessing Value to store the start time of the recording.
        """

        # Log the data from the replay mode
        frame = 0
        while True:
            if (time.time() - start_time.value) > data["time"][frame]:
                # Log the state dictionary
                log_state_dict(
                    state_dict={
                        "metaball/pose": data["pose"][frame],
                        "metaball/force": data["force"][frame],
                    }
                )

                # Log the metaball mesh
                metaball_node = data["node"][frame]
                log_metaball(
                    "metaball",
                    metaball_node,
                    self.metaball_mesh,
                    self.metaball_node_num,
                    self.metaball_def_node,
                    self.metaball_colormap,
                    self.metaball_cmin,
                    self.metaball_cmax,
                )

                # Log the camera images
                log_camera(
                    imgs={
                        "metaball": data["img"][frame],
                    }
                )

                # Increment the frame
                frame += 1

                # Check if the frame is the last one
                if frame == len(data["time"]):
                    return


@rr.shutdown_at_exit
def rerun_server(
    blueprint,
    zmq_queue: Queue,
    recording_queue: Queue,
    is_recording,
    start_time,
) -> None:
    """
    Run the rerun server.

    Args:
        blueprint: The blueprint for the rerun server.
        zmq_queue (Queue): The queue for receiving the data.
        recording_queue (Queue): The queue for recording the data.
        is_recording (Value): A multiprocessing Value indicating whether recording is active.
        start_time (Value): A multiprocessing Value to store the start time of the recording.
    """

    # Initialize the rerun server
    rr.init("Metaball Viewer")
    rr.connect_tcp()
    rr.send_blueprint(blueprint)

    # Initialize the MetaballVis
    metaball_vis = MetaballVis()

    # Run the MetaballVis
    metaball_vis.run(zmq_queue, recording_queue, is_recording, start_time)


@rr.shutdown_at_exit
def rerun_log(
    blueprint,
    data: dict,
    init_ready,
) -> None:
    """
    Run the rerun log.
    
    Args:
        data: The data to be logged.
        init_ready (Value): A multiprocessing Value to indicate that the rerun server is ready.
    """
    
    # Initialize the rerun server
    rr.init("Metaball Viewer")
    rr.connect_tcp()
    rr.send_blueprint(blueprint)

    metaball_vis = MetaballVis()

    # Wait for the initialization
    for i in range(len(init_ready)):
        if init_ready[i] == 0:
            init_ready[i] = 1
            break
    while sum(init_ready) != len(init_ready):
        time.sleep(0.01)

    # Set start time
    start_time = Value("d", time.time())

    # Log the data
    metaball_vis.log(data, start_time)
    
def zmq_subscriber(host: str, port: int, queue: Queue) -> None:
    """
    Start the ZMQ process.

    Args:
        host (str): The host address for the ZMQ subscriber.
        port (int): The port number for the ZMQ subscriber.
        queue (Queue): The queue to put the received data into.
    """
    
    # Initialize the MetaballSubscriber
    subscriber = MetaballSubscriber(host, port)

    # Start the ZMQ subscriber
    start = time.time()
    count = 0
    try:
        while True:
            # Subscribe to the message
            metaball_msg = subscriber.subscribeMessage()

            # Put the data into the queue
            queue.put(parse_data(metaball_msg))
            
            count += 1
            if count == 60:
                print(f"FPS: {60 / (time.time() - start):.2f}, Press Ctrl+C to exit.")
                start = time.time()
                count = 0
    except KeyboardInterrupt:
        print("\nCtrl+C detected. Terminating ZMQ subscriber...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        subscriber.close()
        return