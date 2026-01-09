#!/usr/bin/env python

import re
import zmq
import pathlib
import numpy as np
from typing import Tuple
from datetime import datetime
from metaball_viewer.modules.protobuf import metaball_msg_pb2


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
            hwm (int, optional): High water mark for the publisher socket. Default is 1.
            conflate (bool, optional): Whether to conflate messages. Default is True.
        """
        
        print(f"MetaBall Publisher Address: tcp://{host}:{port}")

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

    def pubishMessage(
        self,
        img: bytes = b"",
        pose: list = np.zeros(6, dtype=np.float32).tolist(),
        force: list = np.zeros(6, dtype=np.float32).tolist(),
        node: list = np.zeros(6, dtype=np.float32).tolist(),
    ) -> None:
        """
        Publish the message.

        Args:
            img (bytes): The image captured by the camera.
            pose (list): The pose of the marker.
            force (list): The force on the bottom surface of the metaball.
            node (list): The node displacement of the metaball.
        """

        # Set the message
        metaball = metaball_msg_pb2.Metaball()
        metaball.timestamp = datetime.now().timestamp()
        metaball.img = img
        metaball.pose[:] = pose
        metaball.force[:] = force
        metaball.node[:] = node

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
    """
    MetaballSubscriber class.

    This class is used to subscribe to Metaball messages using ZeroMQ.

    Attributes:
        context (zmq.Context): The ZMQ context for the subscriber.
        subscriber (zmq.Socket): The ZMQ subscriber socket.
    """

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
            hwm (int, optional): High water mark for the subscriber socket. Default is 1.
            conflate (bool, optional): Whether to conflate messages. Default is True.
        """

        print(f"MetaBall Subscriber Address: tcp://{host}:{port}")

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

    def subscribeMessage(self) -> Tuple[bytes, list, list, list]:
        """
        Subscribe the message.

        Returns:
            data (tuple): metaball data.
                - img (bytes): The image captured by the camera.
                - pose (list): The pose of the marker.
                - force (list): The force on the bottom surface of the metaball.
                - node (list): The node displacement of the metaball.
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
