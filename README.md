# A2A: Academic Paper Summarization


**Your AI-powered research assistant for discovering, summarizing, and reviewing academic papers.**



> A fully autonomous, AI-driven workflow that fetches papers from arXiv, uses local Large Language Models for summarization and quality review, and presents the results in a clean, interactive web UI.


## ✨ Core Features

  * **📚 Automated Search & Fetch:** Finds relevant papers on arXiv based on your research topic.
  * **🧠 Intelligent Summarization:** Leverages a local LLM (`facebook/bart-large-cnn`) to generate concise, abstractive summaries.
  * **🔎 AI-Powered Review:** A second LLM (`facebook/bart-base`) acts as a reviewer, checking the summary against the original text for missing information or inaccuracies.
  * **🌐 Interactive UI:** Built with Gradio for a smooth, user-friendly experience.
  * **🧩 Microservice Architecture:** Each component (fetch, summarize, review) is an independent service, ensuring scalability and maintainability.

## 🏗️ Architecture

This project uses a microservice architecture. The Gradio UI communicates via REST API to a FastAPI Coordinator, which then orchestrates the workflow by calling the various worker agents using JSON-RPC.

```
graph TD
    A[User via Browser] --> B(🖼️ Gradio UI);
    B -->|REST API (HTTP)| C{⚙️ Coordinator (FastAPI)};
    C -->|JSON-RPC| D[📡 Fetcher Agent];
    D -->|HTTP GET| E[📄 arXiv API];
    C -->|JSON-RPC| F[✍️ Summarizer Agent];
    C -->|JSON-RPC| G[🧐 Reviewer Agent];
```

## 🛠️ Tech Stack

| Component             | Technology / Library                                                              |
| --------------------- | --------------------------------------------------------------------------------- |
| **User Interface** | `Gradio`                                                                          |
| **API Gateway** | `FastAPI`                                                                         |
| **Internal RPC** | `jsonrpc-py`, `Werkzeug`                                                          |
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
python -m venv venv
# On Windows:
# venv\Scripts\activate

# On macOS/Linux:
# source venv/bin/activate

# 3. Install the dependencies
pip install -r requirements.txt
```


```text
fastapi
uvicorn[standard]
requests
gradio
jsonrpc-py
Werkzeug
torch
transformers
sentencepiece
PyMuPDF
```

*Note: For optimal performance, you may want to install a CUDA-enabled version of PyTorch by following the instructions on the [official PyTorch website](https://pytorch.org/get-started/locally/).*


## ▶️ How to Run

This application requires **5 separate terminal windows** to run all the microservices.

| Step | Terminal | Service           | Command                                     | Purpose                                     |
| :--- | :------- | :---------------- | :------------------------------------------ | :------------------------------------------ |
| 1    | Terminal 1 | **Fetcher Agent** | `python fetcher_agent.py`                   | 📡 Searches and downloads papers.         |
| 2    | Terminal 2 | **Summarizer Agent**| `python summarizer_agent.py`                | ✍️ Summarizes paper text.                 |
| 3    | Terminal 3 | **Reviewer Agent** | `python reviewer_agent.py`                  | 🧐 Reviews the generated summary.         |
| 4    | Terminal 4 | **Coordinator** | `uvicorn coordinator:app --port 8000`     | ⚙️ Orchestrates the agents.               |
| 5    | Terminal 5 | **Gradio UI** | `python gradio_ui.py`                       | 🖼️ The user-facing web application.       |

After running the final command, open your web browser and navigate to the URL provided in Terminal 5 (usually `http://127.0.0.1:7860`).

## 📂 Project Structure

```
.
├── 📄 coordinator.py      # FastAPI server that orchestrates the agents.
├── 📄 fetcher_agent.py    # JSON-RPC server for fetching papers from arXiv.
├── 📄 summarizer_agent.py # JSON-RPC server for summarizing text.
├── 📄 reviewer_agent.py   # JSON-RPC server for reviewing summaries.
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
