# A2A: Academic Paper Summarization

\<div align="center"\>

**Your AI-powered research assistant for discovering, summarizing, and reviewing academic papers.**

\</div\>

> A fully autonomous, AI-driven workflow that fetches papers from arXiv, uses local Large Language Models for summarization and quality review, and presents the results in a clean, interactive web UI.

\<br\>

\<p align="center"\>
\<img src="[suspicious link removed]" alt="Application Screenshot" width="800"/\>
\</p\>

## ✨ Core Features

  * **📚 Automated Search & Fetch:** Finds relevant papers on arXiv based on your research topic.
  * **🧠 Intelligent Summarization:** Leverages a local LLM (`facebook/bart-large-cnn`) to generate concise, abstractive summaries.
  * **🔎 AI-Powered Review:** A second LLM (`facebook/bart-base`) acts as a reviewer, checking the summary against the original text for missing information or inaccuracies.
  * **🌐 Interactive UI:** Built with Gradio for a smooth, user-friendly experience.
  * **🧩 Microservice Architecture:** Each component (fetch, summarize, review) is an independent FastAPI service, ensuring scalability and maintainability.

## 🏗️ Architecture

This project uses a microservice architecture where all services communicate via standard REST APIs. The Gradio UI calls a central Coordinator, which then orchestrates the workflow by calling the other worker agents.

```mermaid
graph TD
    A[User via Browser] --> B(🖼️ Gradio UI);
    B -->|REST API (HTTP)| C{⚙️ Coordinator Agent (FastAPI)};
    C -->|REST API (HTTP)| D[📡 Fetcher Agent (FastAPI)];
    D -->|HTTP GET| E[📄 arXiv API];
    C -->|REST API (HTTP)| F[✍️ Summarizer Agent (FastAPI)];
    C -->|REST API (HTTP)| G[🧐 Reviewer Agent (FastAPI)];
```

## 🛠️ Tech Stack

| Component             | Technology / Library                                                              |
| --------------------- | --------------------------------------------------------------------------------- |
| **User Interface** | `Gradio`                                                                          |
| **Backend Services** | `FastAPI`, `Uvicorn`                                                              |
| **Internal Communication**| `REST API (HTTP)`, `Requests`                                                      |
| **AI / Machine Learning** | `PyTorch`, `Hugging Face Transformers`                                            |
| **PDF Processing** | `PyMuPDF`                                                                         |
| **Models Used** | `facebook/bart-large-cnn` (Summarizer), `facebook/bart-base` (Reviewer)           |

## 🚀 Getting Started

Follow these steps to set up and run the project on your local machine.

### 1\. Prerequisites

  * Python 3.8+
  * Git
  * **NVIDIA GPU (CUDA)** is highly recommended for reasonable performance.

### 2\. Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/your-repository-name.git
cd your-repository-name

# 2. Create and activate a virtual environment
# For Conda:
conda create --name a2a-app python=3.10 -y
conda activate a2a-app

# For standard venv:
# python -m venv venv
# source venv/bin/activate

# 3. Install the dependencies using the correct pip for your environment
python -m pip install -r requirements.txt
```

\<details\>
\<summary\>Click to view \<strong\>requirements.txt\</strong\>\</summary\>

```text
fastapi
uvicorn[standard]
requests
gradio
torch
transformers
sentencepiece
PyMuPDF
```

*Note: For optimal performance, you may want to install a CUDA-enabled version of PyTorch by following the instructions on the [official PyTorch website](https://pytorch.org/get-started/locally/).*

\</details\>

## ▶️ How to Run

This application requires **5 separate terminal windows** to run all services. Ensure your virtual environment (`a2a-app`) is activated in each terminal.

| Step | Terminal | Service           | Command                                       |
| :--- | :------- | :---------------- | :-------------------------------------------- |
| 1    | Terminal 1 | **Fetcher Agent** | `uvicorn fetcher_agent:app --port 8001`       |
| 2    | Terminal 2 | **Summarizer Agent**| `uvicorn summarizer_agent:app --port 8002`  |
| 3    | Terminal 3 | **Reviewer Agent** | `uvicorn reviewer_agent:app --port 8003`       |
| 4    | Terminal 4 | **Coordinator** | `uvicorn coordinator:app --port 8000`       |
| 5    | Terminal 5 | **Gradio UI** | `python gradio_ui.py`                         |

After running the final command, open your web browser and navigate to the URL provided in Terminal 5 (usually `http://127.0.0.1:7860`).

## 📂 Project Structure

```
.
├── 📄 coordinator.py      # FastAPI server that orchestrates the agents.
├── 📄 fetcher_agent.py    # FastAPI server for fetching papers from arXiv.
├── 📄 summarizer_agent.py # FastAPI server for summarizing text.
├── 📄 reviewer_agent.py   # FastAPI server for reviewing summaries.
├── 📄 gradio_ui.py        # The Gradio web interface for user interaction.
└── 📄 requirements.txt    # Project dependencies.
```

## 💡 Possible Improvements

  * **Dockerize Services:** Containerize each service with Docker for simplified setup and deployment.
  * **Robust Error Handling:** Implement more granular error handling and state reporting to the UI.
  * **Add a Database:** Store results, requests, and user feedback in a database like SQLite or PostgreSQL.
  * **Expand Data Sources:** Add support for other academic sources like PubMed, Semantic Scholar, etc.
  * **Model Selection:** Allow users to choose different summarization or reviewer models via the UI.

## 📄 License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.
