#!/usr/bin/env python3

import os
import numpy as np
import h5py
from tqdm import tqdm


def parse_data(magiclaw_msg) -> dict:
    """
    Parse the Metaball message and return a dictionary of data.
    
    Args:
        magiclaw_msg: The Metaball message to parse.
        
    Returns:
        Dict:
            - pose (np.ndarray): The pose of the metaball.
            - force (np.ndarray): The force applied to the metaball.
            - node (np.ndarray): The metaball mesh data.
            - img (bytes): The image captured by the camera.
    """
    
    data = {
        "img": magiclaw_msg[0],
        "pose": np.array(magiclaw_msg[1]),
        "force": np.array(magiclaw_msg[2]),
        "node": np.array(magiclaw_msg[3]),
        
    }
    
    return data

def save_data(data: list, save_path: str) -> None:
    """
    Save the parsed data to an HDF5 file.
    
    Args:
        data (list): The data to save.
        save_path (str): The path to save the data.
    """
    
    if not os.path.exists(save_path):
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
    with h5py.File(save_path, "w") as f:
        # Collect lists for structured items
        time_list = []
        pose_list = []
        force_list = []
        node_list = []
        
        f.create_group("img")  # Create a group for images
        
        for idx, item in tqdm(enumerate(data), total=len(data), desc="Saving", ncols=100):
            time_list.append(item["time"])
            pose_list.append(item["pose"])
            force_list.append(item["force"])
            node_list.append(item["node"])
            
            # Save images as variable-length byte arrays
            for key in ["img"]:
                img_bytes = item[key]
                img_grp = f.require_group(key)
                if img_bytes is not None:
                    if isinstance(img_bytes, np.ndarray):
                        img_bytes = img_bytes.tobytes()
                    elif isinstance(img_bytes, bytes):
                        pass
                    else:
                        raise TypeError(f"Unsupported type for {key}: {type(img_bytes)}")
                    img_grp.create_dataset(str(idx), data=np.void(img_bytes))
        
        f.create_dataset("time", data=np.array(time_list), compression="gzip")
        f.create_dataset("pose", data=np.array(pose_list), compression="gzip")
        f.create_dataset("force", data=np.array(force_list), compression="gzip")
        f.create_dataset("node", data=np.array(node_list), compression="gzip")
        
        print(f"Data saved to {save_path}")
        

def load_data(file_path: str) -> dict:
    """
    Load data from an HDF5 file.
    
    Args:
        file_path (str): The path to the HDF5 file.
        
    Returns:
        Dict: The loaded data.
    """
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {file_path} does not exist.")
    
    data = {}
    
    with h5py.File(file_path, "r") as f:
        num_frames = len(f["time"])
        
        imgs = []
        for i in range(num_frames):
            
            # Load images as byte arrays
            for key in ["img"]:
                img_data = f[key][str(i)]
                imgs.append(bytes(img_data) if isinstance(img_data, np.void) else img_data)

        data["time"] = np.array(f["time"])
        data["pose"] = np.array(f["pose"])
        data["force"] = np.array(f["force"])
        data["node"] = np.array(f["node"])
        data["img"] = imgs
        
    return data