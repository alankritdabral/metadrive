"""
This script aims to convert nuplan scenarios to ScenarioDescription, so that we can load any nuplan scenarios into
MetaDrive.
"""
import copy
import os
import pickle

import tqdm

from metadrive.engine.asset_loader import AssetLoader
from metadrive.scenario.scenario_description import ScenarioDescription
from metadrive.utils.nuscenes_utils.utils import convert_one_scene
from metadrive.utils.utils import dict_recursive_remove_array
import shutil

try:
    from nuscenes import NuScenes
except ImportError:
    print("Can not find nuscenes-devkit")


def convert_scenarios(version, dataroot, output_path, worker_index=None, verbose=True, force_overwrite=False):
    save_path = copy.deepcopy(output_path)
    output_path = output_path + "_tmp"
    # meta recorder and data summary
    if os.path.exists(output_path):
        shutil.rmtree(output_path)
    os.makedirs(output_path, exist_ok=False)

    # make real save dir
    delay_remove = None
    if os.path.exists(save_path):
        if force_overwrite:
            delay_remove = save_path
        else:
            raise ValueError("Directory already exists! Abort")

    metadata_recorder = {}
    total_scenarios = 0
    desc = ""
    summary_file = "../../assets/nuscenes/dataset_summary.pkl"
    if worker_index is not None:
        desc += "Worker {} ".format(worker_index)
        summary_file = "dataset_summary_worker{}.pkl".format(worker_index)

    # Init.
    nusc = NuScenes(version=version, verbose=verbose, dataroot=dataroot)
    scenes = nusc.scene
    for scene in tqdm.tqdm(scenes):
        sd_scene = convert_one_scene(scene["token"], nusc)
        sd_scene = sd_scene.to_dict()
        ScenarioDescription.sanity_check(sd_scene, check_self_type=True)
        export_file_name = "sd_{}_{}.pkl".format("nuscenes_" + version, scene["token"])
        p = os.path.join(output_path, export_file_name)
        with open(p, "wb") as f:
            pickle.dump(sd_scene, f)
        metadata_recorder[export_file_name] = copy.deepcopy(sd_scene[ScenarioDescription.METADATA])
    # rename and save
    if delay_remove is not None:
        shutil.rmtree(delay_remove)
    os.rename(output_path, save_path)
    summary_file = os.path.join(save_path, summary_file)
    with open(summary_file, "wb") as file:
        pickle.dump(dict_recursive_remove_array(metadata_recorder), file)
    print("Summary is saved at: {}".format(summary_file))
    assert delay_remove == save_path


if __name__ == "__main__":
    output_path = AssetLoader.file_path("nuscenes", return_raw_style=False)
    version = 'v1.0-mini'
    verbose = True
    dataroot = '/home/shady/data/nuscenes'
    worker_index = None
    force_overwrite = True
    convert_scenarios(version, dataroot, output_path, force_overwrite=force_overwrite)