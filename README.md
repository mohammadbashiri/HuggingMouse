# HuggingMouse

![alt text](https://github.com/mariakesa/HuggingMouse/blob/main/logo_CC0_attention.jpg)

HuggingMouse is a data analysis library that combines AllenSDK (Allen Brain Observatory), HuggingFace Transformers, Sklearn
and Pandas. 

You can install the library via pip:

    pip install HuggingMouse

or clone this repo and run:

    pip install .

The documentation of the project is at: https://huggingmouse.readthedocs.io/en/latest/

[Allen Brain Observatory](https://allensdk.readthedocs.io/en/latest/brain_observatory.html) is a massive repository of calcium imaging recordings from the mouse visual cortex during presentation of various visual stimuli ([see also](https://github.com/AllenInstitute/brain_observatory_examples/blob/master/Visual%20Coding%202P%20Cheat%20Sheet%20October2018.pdf)). Currently, HuggingMouse supports running regression analyses on neural data while mice are viewing [three different natural movies](https://observatory.brain-map.org/visualcoding/stimulus/natural_movies). The code uses the Strategy design pattern to make it easy to run regression analyses with any HuggingFace vision model that can turn images into embeddings (currently the code extracts CLS tokens). Any regression model that has a sklearn like API will work. The result of the regression is measured by a metric function from sklearn metrics module and trial-by-trial analyses are stored in a Pandas dataframe, which can be further processed with statistical analyses. 

The following sections go through the code step by step. The entire script is avaiable here: https://github.com/mariakesa/HuggingMouse/blob/main/scripts/example_script.py

### Setting environment variables

In order to run the analyses three environment variables have to be set. These environmental variables are paths that are used to cache Allen data comming from the API, save HuggingFace model embeddings of experimental stimuli (natural movies)
and save the csv files that come from regression analyses. 

These three environment variables are: HGMS_ALLEN_CACHE_PATH, HGMS_TRANSF_EMBEDDING_PATH, HGMS_REGR_ANAL_PATH

There are two ways to set these variables. First, you can use the os module in Python:

    import os

    os.environ["HGMS_ALLEN_CACHE_PATH"] = ...Allen API cache path as string...
    os.environ["HGMS_TRANSF_EMBEDDING_PATH"] = ...stimulus embedding path as string...
    os.environ["HGMS_REGR_ANAL_PATH"] = ...path to store model metrics csv's as string...

Alternatively, you can save the same paths in a .env file like this:

    HGMS_ALLEN_CACHE_PATH=...path... 
    HGMS_TRANSF_EMBEDDING_PATH=...path...
    HGMS_REGR_ANAL_PATH=...path...

and call the dotenv library to read in these environment variables in your script that uses HuggingMouse:

    from dotenv import load_dotenv

    load_dotenv('.env')

Note that the dotenv library has to be installed for this to work.

### Selecting experimental container for analysis

HuggingMouse has a helper class for choosing the experimental container (one transgenic animal).

    from HuggingMouse.allen_api_utilities import AllenExperimentUtility

    info_utility = AllenExperimentUtility()
    #These functions will print some information to help select the
    #experimental container id to work on. 
    info_utility.view_all_imaged_areas()
    info_utility.visual_areas_info()
    #Let's grab the first eperiment container id in the VISal area. 
    id = info_utility.experiment_container_ids_imaged_areas(['VISal'])[0]


### Visualizing trial averaged data

You can use any sklearn decomposition (PCA, NMF) or manifold method (TSNE, SpectralEmbedding) or
your own custom model with a fit_transform method to visualize the patterns in the neural data. 
This is currently possible with trial averaged data. The visulize function takes the session and 
the stimulus that the uniquely identify a sequence of trials and embeds the data
using the provided model. 

    dim_reduction_model = PCA(n_components=3)
    trial_averaged_data = MakeTrialAveragedData().get_data(id)
    visualizer = VisualizerDimReduction(dim_reduction_model)
    visualizer.info()
    visualizer.visualize(trial_averaged_data,
                        'three_session_A', 'natural_movie_one')

    dim_reduction_model2 = TSNE(n_components=3)
    visualizer2 = VisualizerDimReduction(dim_reduction_model2)
    visualizer2.visualize(trial_averaged_data,
                        'three_session_A', 'natural_movie_one')

### Fitting regression models

Fitting a regression model takes a few lines of code in HuggingMouse. As with the 
dimensionality reduction in the previous segment, you can use any sklearn regression model
or any other model with a sklearn like API (why not an RNN?). Any HuggingFace model that can
embed images in a CLS token will work as an image embedding model. Regression creates a csv file
where each trial is regressed with a separate random seed for train and test split. Currently,
the train-test split allocates 30% of the timepoints to training data and 70% to test data (
video data have a lot of temporal and spatial redundancy, so we make the task harder for the model.s
). The regression class also needs a metric from sklearn metrics (regression metric, not classification metric)
to compute the scores in the csv. The analysis files will be saved in the directory specified by the
HGMS_REGR_ANAL_PATH path. At this path the data_index_df.csv will also be updated each time a new
analysis is run. This file stores the model regression_model, transformer_model, transformer_model_prefix,
allen_container_id and the hash that specifies the file name. It can be used to combine analyses across
multiple regression experiments. 

    regression_model = Ridge(10)
    metrics = [r2_score, mean_squared_error, explained_variance_score]
    # Let's use the most popular Vision Transformer model from HuggingFace
    model = ViTModel.from_pretrained('google/vit-base-patch16-224')
    VisionEmbeddingToNeuronsRegressor(
        regression_model, metrics, model=model).execute(id)

### Don't panic!

If everything I just wrote sounds like Chinese to you, hold tight, I'm preparing a Jupyter book 
that goes more into depth on every aspect of the analysis and condenses the scientific literature
on studying animal vision with deep learning models:-)

We are going after the mysteries of the brain-- this is what calcium imaging raw data looks like:

![Calcium Imaging](https://github.com/mariakesa/HuggingMouse/blob/main/calcium_movie.gif)

The gif is courtesy of [Andermann lab](https://www.andermannlab.com/), used with permission.



