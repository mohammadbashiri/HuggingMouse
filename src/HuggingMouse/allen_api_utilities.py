from allensdk.core.brain_observatory_cache import BrainObservatoryCache
from pathlib import Path
import os
from HuggingMouse.custom_exceptions import AllenCachePathNotSpecifiedError, TransformerEmbeddingCachePathNotSpecifiedError

class AllenExperimentUtility:
    def __init__(self):
        allen_cache_path = os.environ.get('HGMS_ALLEN_CACHE_PATH')
        if allen_cache_path is None:
            raise AllenCachePathNotSpecifiedError()
        transformer_embedding_cache_path=os.environ.get('HGMS_TRANSF_EMBEDDING_PATH')
        if transformer_embedding_cache_path is None:
            raise TransformerEmbeddingCachePathNotSpecifiedError()
        self.boc = BrainObservatoryCache(manifest_file=str(Path(allen_cache_path) / 'brain_observatory_manifest.json'))
        
    def view_all_imaged_areas(self):
        print(self.boc.get_all_targeted_structures())

    def view_all_cre_lines(self):
        print(self.boc.get_all_cre_lines())

    def imaged_area_info(self, imaged_area):
        print(0)

    def experiment_container_ids_imaged_areas(self, imaged_areas):
        experiment_containers=self.boc.get_experiment_containers(targeted_structures=imaged_areas)
        ecids=[exp_c['id'] for exp_c in experiment_containers]
        print('These are experimental containers\'s that contain query imaged areas: ',
              experiment_containers)
        print('These are experimental container id\'s corresponding to imaged areas', ecids)
        return ecids