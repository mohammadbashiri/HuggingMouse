import sys
sys.path.append('/home/maria/HuggingMouse/src')
from dotenv import load_dotenv
load_dotenv('.env')
from transformers import AutoImageProcessor
from HuggingMouse.utils import make_container_dict, generate_random_state, regression, process_single_trial, hash_df
from allensdk.core.brain_observatory_cache import BrainObservatoryCache
from pathlib import Path
import pickle
import os
from HuggingMouse.make_embeddings import MakeEmbeddings
import pandas as pd
from sklearn.base import clone
from HuggingMouse.custom_exceptions import AllenCachePathNotSpecifiedError, TransformerEmbeddingCachePathNotSpecifiedError, RegressionOutputCachePathNotSpecifiedError


class VisionEmbeddingToNeuronsRegressor:
    def __init__(self, model, regression_model):
        allen_cache_path = os.environ.get('HGMS_ALLEN_CACHE_PATH')
        if allen_cache_path is None:
            raise AllenCachePathNotSpecifiedError()
        transformer_embedding_cache_path=os.environ.get('HGMS_TRANSF_EMBEDDING_PATH')
        if transformer_embedding_cache_path is None:
            raise TransformerEmbeddingCachePathNotSpecifiedError()
        self.regr_analysis_results_cache=os.environ.get('HGMS_REGR_ANAL_PATH')
        if self.regr_analysis_results_cache is None:
            raise RegressionOutputCachePathNotSpecifiedError()
        self.model = model
        self.model_name_str = model.name_or_path
        self.processor = AutoImageProcessor.from_pretrained(self.model_name_str)
        self.model_prefix=self.model.name_or_path.replace('/', '_') 
        self.regression_model = regression_model
        self.regression_model_class = regression_model.__class__.__name__
        embedding_file_path = os.path.join(transformer_embedding_cache_path, f"{self.model_prefix}_embeddings.pkl")
        if not os.path.exists(embedding_file_path):
            self.embeddings=MakeEmbeddings(self.processor, self.model).execute()
        else:
            with open(embedding_file_path, 'rb') as f:
                self.embeddings = pickle.load(f)
        self.boc = BrainObservatoryCache(manifest_file=str(Path(allen_cache_path) / Path('brain_observatory_manifest.json')))
        self.eid_dict = make_container_dict(self.boc)
        self.stimulus_session_dict= {
            'three_session_A': ['natural_movie_one', 'natural_movie_three'],
            'three_session_B': ['natural_movie_one'],
            'three_session_C': ['natural_movie_one', 'natural_movie_two'],
            'three_session_C2': ['natural_movie_one', 'natural_movie_two']
        }
        print(self.embeddings.keys())
        self.random_state_dct=generate_random_state(seed=7, stimulus_session_dict=self.stimulus_session_dict)

    def make_regression_data(self, container_id, session):
        session_eid  = self.eid_dict[container_id][session]
        dataset = self.boc.get_ophys_experiment_data(session_eid)
        cell_ids = dataset.get_cell_specimen_ids()
        dff_traces = dataset.get_dff_traces()[1]
        session_stimuli = self.stimulus_session_dict[session]
        session_dct = pd.DataFrame()
        regression_vec_dct={}
        session_dct['cell_ids'] = cell_ids
        #regression_vec_dct['cell_ids'] = cell_ids
        #Compile the sessions into the same column to avoind NAN's
        #and make the data processing a bit easier
        if session=='three_session_C2':
            sess='three_session_C'
        else:
            sess=session
        for s in session_stimuli:
            movie_stim_table = dataset.get_stimulus_table(s)
            embedding=self.embeddings[s]
            #There are only 10 trials in each session-stimulus pair
            for trial in range(10):
                random_state=self.random_state_dct[session][s][trial]
                data=process_single_trial(movie_stim_table, dff_traces, trial, embedding, random_state=random_state)
                #Code: session-->model-->stimulus-->trial
                var_exps = regression(data,self.regression_model)
                session_dct[str(sess)+'_'+str(s)+'_'+str(trial)] = var_exps
                #regression_vec_dct[str(sess)+'_'+str(m)+'_'+str(s)+'_'+str(trial)]=regr_vecs
        return session_dct#, regression_vec_dct
    
    def update_data_index_df(self,container_id,hash):
        data_index_df_path=Path(self.regr_analysis_results_cache)/Path('data_index_df.csv')
        
        if data_index_df_path.exists():
            data_index_df=pd.read_csv(data_index_df_path)
        else:
            data_index_df=pd.DataFrame()

        current_row={
            'regression_model':self.regression_model_class,
            'transformer_model':self.model_name_str,
            'transformer_model_prefix': self.model_prefix,
            'allen_container_id': container_id,
            'hash': hash
        }

        data_index_df = data_index_df.append(pd.Series(current_row, name=len(data_index_df)), ignore_index=False)
        print(data_index_df)

        
    
    def execute(self, container_id):
        # Create an empty DataFrame to hold the merged data
        merged_data = None

        for session, session_dict in self.stimulus_session_dict.items():
            try:
                session_dct = self.make_regression_data(container_id, session)
                session_df = pd.DataFrame(session_dct)

                if merged_data is None:
                    merged_data = session_df
                else:
                    # Perform an outer join on 'cell_id' column
                    merged_data = pd.merge(merged_data, session_df, on='cell_ids', how='outer')

            except: 
                continue

        
        hash=hash_df(merged_data)

        self.update_data_index_df(container_id, hash)

        #Save data
        data_save_path=Path(self.regr_analysis_results_cache)/Path(str(hash)+'.csv')

        merged_data.to_csv(data_save_path)

        return merged_data

if __name__=='__main__':
    from dotenv import load_dotenv
    import os
    top_10_keys=['google/vit-base-patch16-224', 'timm/mobilenetv3_large_100.ra_in1k']

    load_dotenv('.env')

    print(os.environ.get("HGMS_ALLEN_CACHE_PATH"))

    import sys
    #sys.path.append('/home/maria/HuggingMouse/src')
    #from HuggingMouse.regressors import VisionEmbeddingToNeuronsRegressor
    from sklearn.linear_model import Ridge
    from sklearn.decomposition import PCA
    from HuggingMouse.allen_api_utilities import AllenExperimentUtility
    from dotenv import load_dotenv
    from transformers import AutoModel
    import os

    regression_model=Ridge(10)
    m=top_10_keys[0]
    model = AutoModel.from_pretrained(m)
    exps=AllenExperimentUtility()
    exps.view_all_imaged_areas()
    id=exps.experiment_container_ids_imaged_areas(['VISal'])[0]
    VisionEmbeddingToNeuronsRegressor(model,regression_model).execute(id)
