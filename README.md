# ReplitLM
Guides, code and configs for the ReplitLM model family.

_This is being continuously updated to add more ways to use and build on top of our models._

## Table of Contents
- [Models](#models)
- [Releases](#releases)
- [Usage](#usage)
    - [Hosted Demo](#hosted-demo)
    - [Using with Hugging Face Transformers](#using-with-hugging-face-transformers)
    - [AI App Builder (local)](#ai-app-builder-local)
- [Training and Fine-tuning](#training-and-fine-tuning)
    - [Training with LLM Foundry](#training-with-llm-foundry)
- [Instruction Tuning](#instruction-tuning)
    - [Alpaca-style Instruct Tuning with Hugging Face Transformers](#alpaca-style-instruct-tuning-with-hugging-face-transformers)
    - [Instruct Tuning with LLM Foundry](#instruct-tuning-with-llm-foundry)
- [FAQs](#faqs)



## Models
| Model | Checkpoint [CC BY-SA 4.0] | Vocabulary [CC BY-SA 4.0] | Code [Apache 2.0] |
| --- | --- | --- | --- |
| replit-code-v1-3b | [Download Link](https://huggingface.co/replit/replit-code-v1-3b/blob/main/pytorch_model.bin) | [Download](https://huggingface.co/replit/replit-code-v1-3b/resolve/main/spiece.model) | [Repo](https://github.com/replit/ReplitLM/tree/main/replit-code-v1-3b) |
| replit-code-v1_5-3b | (Coming Soon) | (Coming Soon) | Coming Soon |


## Releases
May 2, 2023: [`replit-code-v1-3b`](https://github.com/replit/ReplitLM/tree/main/replit-code-v1-3b)



## Usage

### Hosted Demo

We also have a GPU-powered Space for the `replit-code-v1-3b` model where you can use the model directly!

[GPU-powered Hosted Demo](https://huggingface.co/spaces/replit/replit-code-v1-3b-demo)

### Using with Hugging Face Transformers

All released Replit models are available on Hugging Face under the [Replit organization page](https://huggingface.co/replit) and can be used with the Hugging Face Transformers library.

You can use the Replit models with Hugging Face Transformers library. The README for each released model has instructions on how to use the model with Hugging Face Transformers. 
Make sure you set the `clean_up_tokenization_spaces=False` when decoding with the tokenizer as well use the recommended post processing given in the README. 

| Model | README |
| --- | --- |
| replit-code-v1-3b | [Documentation](https://huggingface.co/replit/replit-code-v1-3b) |

### AI App Builder (local)

This repo now includes a minimal AI App Builder web UI (FastAPI) that uses ReplitLM to generate small runnable apps (Streamlit, Gradio, or plain Python) from a natural‑language description. It returns a downloadable .zip project.

Run locally:

1) Install dependencies
```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

2) Start the server
```
uvicorn app.main:app --reload
```

3) Open http://127.0.0.1:8000 and submit an app idea. The server will generate a project zip containing:
- app.py
- requirements.txt
- README.md
- run.sh

Notes:
- The generator first tries to load weights from the local `replit-code-v1-3b/` folder. If not found, it falls back to Hugging Face `replit/replit-code-v1-3b`.
- GPU is used automatically if available (float16). CPU also works for short prompts but will be slower.
- Streamlit apps can be run with `streamlit run app.py`.

## Training and Fine-tuning

### Training with LLM Foundry

We recommend any further training, pre-training and finetuning of the Replit models with MosaicML's [LLM Foundry](https://github.com/mosaicml/llm-foundry) and [Composer](https://github.com/mosaicml/composer).

Our Replit models are compatible with LLM Foundry and can be trained/tuned in a highly optimized way with LLM Foundry + Composer using state of the art training techniques, architectural components, optimizers, and more. All models, LLM Foundry and the Composer training framework are Pytorch-based. Using these you can train the Replit models on your own datasets.

The following steps give you the outline of what needs to be done to train the models with links to the LLM Foundry documentation sections needed for each step:

#### (0) Install LLM Foundry and Requirements

**Install LLM Foundry**
You can get started with LLM Foundry by following their README.

At a high-level, LLM Foundry is used by defining a configuration yaml and then running  `train/train.py` training script in the LLM Foundry repo with the defined configuration yaml using a command like `composer train/train.py <configuration_yaml_path> <extra_args>`.
The [scripts/train/yamls](https://github.com/mosaicml/llm-foundry/tree/main/scripts/train/yamls) dir contains example YAMLs for both finetuning and pretaining. 

**Install Other Requirements for the Replit Models**
You will then have to install a few other dependencies specified in the `requirements.txt`.

#### (1) Convert and Save Your Dataset

To train with LLM Foundry, you need to convert your dataset to the [Mosaic StreamingDataset](https://github.com/mosaicml/streaming) format. 

The types of dataset sources supported are JSON datasets and Hugging Face Datasets.

The [Data Preparation](https://github.com/mosaicml/llm-foundry/tree/main/scripts/data_prep) documentation in LLM Foundry gives the steps on how to do this.

:warning: **Important** :warning:

When running the `convert_dataset_hf.py` or `convert_dataset_json.py` in the steps above, you will have to specify that you are using the Replit tokenizer by passing in the argument ` --tokenizer replit/replit-code-v1-3b`.
A key step (due to the current implementation of `llm-foundry`) is to edit `scripts/data_prep/convert_dataset_hf.py` by passing the `trust_remote_code=True` kwarg to the `AutoTokenizer.from_pretrained` call when the tokenizer is loaded in the `main()` method.

... (Original README continues unchanged below) ...

## Instruction Tuning
You can instruct-tune our ReplitLM models for your own use case. For most instruct-tuning use cases, we recommend starting from the Hugging Face examples below. Otherwise, we also provide a detailed guide to do Instruction Tuning with LLM Foundry.

### Alpaca-style Instruct Tuning with Hugging Face Transformers
You can instruct-tune the `replit-code-v1-3b` model on Alpaca-style datasets using the `transformers` library.

To accomplish that, you will need an instruct tuning dataset that is already in Alpaca-style format, such as:
- [Stanford Alpaca](https://github.com/tatsu-lab/stanford_alpaca)
- [Code Alpaca](https://github.com/sahil280114/codealpaca)

Open source contributor [Teknium](https://github.com/teknium1) has forked the original Alpaca repo to the [stanford_alpaca-replit](https://github.com/teknium1/stanford_alpaca-replit) repo that is pre-configured to run with our models. We strongly recommend you use this as your starting point.

The repo contains instructions on how to setup and run the trainer. The required Alpaca-style dataset format is described [here](https://github.com/teknium1/stanford_alpaca-replit#dataset-format). Any dataset formatted Alpaca-style will work with the trainer. For example, the [Code Alpaca dataset](https://github.com/sahil280114/codealpaca) can be used to instruct tune our model using the training script in [Teknium](https://github.com/teknium1)'s repo. 

### Instruct Tuning with LLM Foundry
... (rest of original content unchanged) ...

## FAQs
- What dataset was this trained on?
    - [Stack Dedup](https://huggingface.co/datasets/bigcode/the-stack-dedup)
- What languages was the model trained on?
    - The training mixture includes 20 different languages, listed here in descending order of number of tokens: Markdown, Java, JavaScript, Python, TypeScript, PHP, SQL, JSX, reStructuredText, Rust, C, CSS, Go, C++, HTML, Vue, Ruby, Jupyter Notebook, R, Shell
- [How many GPUs do I need to train a LLM?](https://github.com/mosaicml/llm-foundry/blob/main/scripts/train/README.md#how-many-gpus-do-i-need-to-train-a-llm)
- [Optimizing Performance](https://github.com/mosaicml/llm-foundry/blob/main/scripts/train/README.md#how-many-gpus-do-i-need-to-train-a-llm)



