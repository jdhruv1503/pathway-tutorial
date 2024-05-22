# Pathway tutorial
Boilerplate files to convert Pathway's contextful example to LiteLLM/HuggingFace models and running it locallly on Windows

## How to get started

To get started, run Pathway's `contextful` example (located in the `Colab Examples` folder) on [Google Colab](https://colab.research.google.com/). Alternatively, run the `contextful-free` example if you don't have an OpenAI API Key.

The `contextful-free` example requires a Groq API key, which you can get for free [here](https://console.groq.com).

## How to run locally

Use the `contextful` and `contextful-free` files (located in the `Windows Examples` folder) with Docker.

To do this, first install Docker Desktop: get it [here](https://docs.docker.com/desktop/install/windows-install/)

Then, pull the folders, open a command prompt in the location where `Dockerfile` is located, and do: `docker build . -t myimage` followed by `docker run -v ${PWD}/data:/app/_data --net=host myimage`. NOTE: This assumes the data folder is at `data` alongside the Python file, but you can change this by changing the path in the second command!
