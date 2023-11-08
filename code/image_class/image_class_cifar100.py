from datasets import load_dataset, Dataset
from transformers import pipeline, AutoTokenizer

from codecarbon import EmissionsTracker
from huggingface_hub import HfApi, ModelFilter
import logging
import torch
import huggingface_hub
import einops

import os

# Create a dedicated logger (log name can be the CodeCarbon project name for example)
_logger = logging.getLogger("image_class_testing")
_channel = logging.FileHandler('/fsx/sashaluc/logs/image_class_testing_cifar100.log')
_logger.addHandler(_channel)
_logger.setLevel(logging.INFO)

## Load models

hf_api=HfApi()
models = hf_api.list_models(
    filter=ModelFilter(
		task="image-classification"),
    sort="downloads", direction=-1, limit=8)

im_classif_models =  [l.modelId for l in models]
### Load prompting datasets

def dset_gen():
    dset = load_dataset("cifar100", streaming=True, split="test")
    sample = dset.take(1000)
    for row in sample:
        im = row['img'].resize((640, 480), resample=0).convert('RGB')
        row['img'] = im
        yield row

dset = Dataset.from_generator(dset_gen)

for model in im_classif_models:
    print(model)
    tracker = EmissionsTracker(project_name=model, measure_power_secs=1, logging_logger=_logger, output_file='/fsx/sashaluc/emissions/image_class_cifar100_resized.csv')
    tracker.start()
    tracker.start_task("load model")
    classifier = pipeline("image-classification", model=model, device=0 )
    model_emissions = tracker.stop_task()
    tracker.start_task("query model")
    count=0
    for d in dset:
        count+=1
        classifier(d['img'])
    model_emissions = tracker.stop_task()
    print('================'+str(count)+'================')
    _ = tracker.stop()
    torch.cuda.empty_cache()
