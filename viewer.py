#!/usr/bin/env python3

"""
Metaball Viewer
==========

This repository is to visualize the Metaball in live (default) or replay mode.

To run the viewer in live mode:

```bash
python viewer.py -m live
```

To run the viewer in replay mode:

```bash
python viewer.py -m replay -d folder_path
```

where `folder_path` is the path of the folder which contains all above data.

During the live mode, the viewer will receive the data from the phone through ZMQ.
Press "Ctrl+C" to exit the viewer.
Press "r" to start recording the data.
Press "s" to stop recording and save the data.

During the replay mode, the viewer will read the data from the specified folder.

Data is visualized through rerun, including:
    - Metaball mesh: The 3D mesh of the metaball.
    - Camera image: The image captured by the inner camera.
    - Pose: The pose of the metaball.
    - Force: The force applied to the metaball.

The blueprint of the viewer is defined in the `blueprint` method, which includes:
    - A 3D scene view for the metaball mesh.
    - A 2D view for the camera image.
    - Time series views for the pose and force of the metaball.
"""

import sys
import os
import argparse
import time
import yaml
import rerun as rr
from pynput import keyboard
from multiprocessing import Process, Queue, Array, Value
from utils.log_utils import gen_blueprint
from utils.process_utils import rerun_server, rerun_log, zmq_subscriber
from utils.event_utils import KeyHandler
from utils.data_utils import load_data


def main(
    mode: str = "live",
    data_path: str = "",
) -> None:
    """
    Main function to run the viewer.

    Args:
        mode (str): The mode of the viewer, either "live" or "replay".
        data_path (str): The path to the data folder for replay mode.
    """

    print("{:=^80}".format(" Metaball Viewer"))

    # Initialize the rerun server
    print("Initializing rerun ...")
    rr.init("Metaball Viewer")
    rr.spawn(connect=False)

    # Send the blueprint
    print("Sending blueprint ...")
    blueprint = gen_blueprint()

    print("Viewer mode:", mode)

    # Live mode
    if mode == "live":
        # Queues for ZMQ and recording
        zmq_queue = Queue()
        recording_queue = Queue()

        # Flag for recording state
        is_recording = Value("i", 0)

        # Flag for start time
        start_time = Value("d", time.time())

        # Load viewer parameters from the config file
        with open(os.path.join("configs", "viewer.yaml"), "r") as f:
            viewer_params = yaml.load(f, Loader=yaml.Loader)

        # Initialize the rerun and ZMQ processes
        print("Initializing rerun and zmq processes ...")
        process_list = []

        # Create the rerun server process
        process_list.append(
            Process(
                target=rerun_server,
                args=(
                    blueprint,
                    zmq_queue,
                    recording_queue,
                    is_recording,
                    start_time,
                ),
            )
        )

        # Create the ZMQ subscriber process
        process_list.append(
            Process(
                target=zmq_subscriber,
                args=(
                    viewer_params["metaball"]["host"],
                    viewer_params["metaball"]["port"],
                    zmq_queue,
                ),
            )
        )

        try:
            # Start the key press listener
            print("Start the key press listener...")
            print("\033[91mPress 'r' to start recording\033[0m")
            print("\033[91mPress 's' to stop recording and save the data\033[0m")
            print("\033[91mPress Ctrl+C to EXIT\033[0m")
            key_handler = KeyHandler(is_recording, start_time, recording_queue)
            listener = keyboard.Listener(on_press=key_handler.on_press)
            listener.daemon = True
            listener.start()

            # Start rerun process
            print("Starting rerun process...")
            for i in range(1, len(process_list)):
                process_list[i].daemon = True
                process_list[i].start()

            process_list[0].start()
            process_list[0].join()
        except KeyboardInterrupt:
            print("\nCtrl+C detected. Exiting...")
            sys.exit(0)
        finally:
            # Shut down the zmq and rerun processes
            for process in process_list:
                if process.is_alive():
                    print(f"Stopping process {process.name}...")
                    process.terminate()
                    process.join(timeout=1.0)
            listener.stop()
            print("All processes have been stopped.")

    elif mode == "replay":
        if data_path == "":
            raise ValueError("\033[31mPLEASE SPECIFY DATA PATH\033[0m")

        # Load HDF5 file
        print("HDF5 file path:", data_path)
        if not os.path.exists(data_path):
            raise ValueError("\033[31mHDF5 file does not exist\033[0m")
        if not os.path.isfile(data_path):
            raise ValueError("\033[31mHDF5 file is not a file\033[0m")
        print("Reading HDF5 file...")
        data = load_data(data_path)

        # Initialize init_ready
        init_ready = Array("i", [0] * 1)

        # Initialize rerun process
        print("Initializing rerun processes ...")
        rerun_process = Process(
            target=rerun_log,
            args=(
                blueprint,
                data,
                init_ready,
            ),
        )

        # Start rerun process
        print("Logging Data...")
        print("This may take a while, please wait...")
        rerun_process.start()
    else:
        raise ValueError("Ivalid mode. Choose 'live' or 'replay'.")


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-m", "--mode", default="live", type=str, help="set the mode of interface"
    )
    parser.add_argument(
        "-d", "--data_path", required=False, type=str, help="select the data to replay"
    )
    args = parser.parse_args()

    main(mode=args.mode, data_path=args.data_path)
