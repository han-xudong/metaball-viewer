#!/usr/bin/env python

import re
import zmq
import pathlib
import numpy as np
from typing import Tuple
from datetime import datetime
from modules.protobuf import metaball_msg_pb2


class MetaballPublisher:
    """
    MetaballPublisher class.

    This class is used to publish Metaball messages using ZeroMQ.

    Attributes:
        context (zmq.Context): The ZMQ context for the publisher.
        publisher (zmq.Socket): The ZMQ publisher socket.
    """

    def __init__(
        self,
        host: str,
        port: int,
        hwm: int = 1,
        conflate: bool = True,
    ) -> None:
        """
        Publisher initialization.

        Args:
            host (str): The host address of the publisher.
            port (int): The port number of the publisher.
            hwm (int): High water mark for the publisher socket. Default is 1.
            conflate (bool): Whether to conflate messages. Default is True.
        """

        print("{:-^80}".format(" Metaball Publisher Initialization "))
        print(f"Address: tcp://{host}:{port}")

        # Create a ZMQ context
        self.context = zmq.Context()
        # Create a ZMQ publisher
        self.publisher = self.context.socket(zmq.PUB)
        # Set high water mark
        self.publisher.set_hwm(hwm)
        # Set conflate
        self.publisher.setsockopt(zmq.CONFLATE, conflate)
        # Bind the address
        self.publisher.bind(f"tcp://{host}:{port}")

        # Read the protobuf definition for Metaball message
        with open(
            pathlib.Path(__file__).parent.parent / "protobuf/metaball_msg.proto",
        ) as f:
            lines = f.read()
        messages = re.search(r"message\s+Metaball\s*{(.*?)}", lines, re.DOTALL)
        body = messages.group(1)
        print("Message Metaball")
        print("{\n" + body + "\n}")

        print("Metaball Publisher Initialization Done.")
        print("{:-^80}".format(""))

    def pubishMessage(
        self,
        img_bytes: bytes = b"",
        pose: list = np.zeros(6, dtype=np.float32).tolist(),
        force: list = np.zeros(6, dtype=np.float32).tolist(),
        node: list = np.zeros(6, dtype=np.float32).tolist(),
    ) -> None:
        """
        Publish the message.

        Args:
            img: The image captured by the camera.
            pose: The pose of the marker (numpy array or list).
            force: The force on the bottom surface of the metaball (numpy array or list).
            node: The node displacement of the metaball (numpy array or list).
        """

        # Set the message
        metaball = metaball_msg_pb2.Metaball()
        metaball.timestamp = datetime.now().timestamp()
        metaball.img = img_bytes
        metaball.pose[:] = pose.flatten().tolist()
        metaball.force[:] = force.flatten().tolist()
        metaball.node[:] = node.flatten().tolist()

        # Publish the message
        self.publisher.send(metaball.SerializeToString())

    def close(self):
        """
        Close ZMQ socket and context to prevent memory leaks.
        """

        if hasattr(self, "publisher") and self.publisher:
            self.publisher.close()
        if hasattr(self, "context") and self.context:
            self.context.term()


class MetaballSubscriber:
    def __init__(
        self,
        host: str,
        port: int,
        hwm: int = 1,
        conflate: bool = True,
    ) -> None:
        """
        Subscriber initialization.

        Args:
            host (str): The host address of the subscriber.
            port (int): The port number of the subscriber.
            hwm (int): High water mark for the subscriber socket. Default is 1.
            conflate (bool): Whether to conflate messages. Default is True.
        """

        print("{:-^80}".format(" Metaball Subscriber Initialization "))
        print(f"Address: tcp://{host}:{port}")

        # Create a ZMQ context
        self.context = zmq.Context()
        # Create a ZMQ subscriber
        self.subscriber = self.context.socket(zmq.SUB)
        # Set high water mark
        self.subscriber.set_hwm(hwm)
        # Set conflate
        self.subscriber.setsockopt(zmq.CONFLATE, conflate)
        # Connect the address
        self.subscriber.connect(f"tcp://{host}:{port}")
        # Subscribe the topic
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

        # Read the protobuf definition for Metaball message
        with open(
            pathlib.Path(__file__).parent.parent / "protobuf/metaball_msg.proto",
        ) as f:
            lines = f.read()
        messages = re.search(r"message\s+Metaball\s*{(.*?)}", lines, re.DOTALL)
        body = messages.group(1)
        print("Message Metaball")
        print("{\n" + body + "\n}")

        print("Metaball Subscriber Initialization Done.")
        print("{:-^80}".format(""))

    def subscribeMessage(self) -> Tuple[bytes, list, list, list]:
        """Subscribe the message.

        Args:
            timeout: Maximum time to wait for a message in milliseconds.
                    Default is 1000ms (1 second).

        Returns:
            img: The image captured by the camera.
            pose: The pose of the marker.
            force: The force on the bottom surface of the metaball.
            node: The node displacement of the metaball.

        Raises:
            zmq.ZMQError: If no message is received within the timeout period.
        """

        # Receive the message
        metaball = metaball_msg_pb2.Metaball()
        metaball.ParseFromString(self.subscriber.recv())
        return (
            metaball.img,
            metaball.pose,
            metaball.force,
            metaball.node,
        )

    def close(self):
        """
        Close ZMQ socket and context to prevent memory leaks.
        """

        if hasattr(self, "subscriber") and self.subscriber:
            self.subscriber.close()
        if hasattr(self, "context") and self.context:
            self.context.term()
