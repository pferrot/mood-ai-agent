# Mood AI Agent

A lightweight AI agent that evaluates the emotional mood of a person from a text input.  
Built with **LangChain** + **Ollama** (Qwen model), served via **FastAPI**, and deployable to **Kubernetes**.

---

## Architecture

```
POST /analyze
     │
     ▼
 FastAPI app  ──►  LangChain agent  ──►  Ollama (Qwen)  ──►  mood string (≤20 words)
```

---

## Prerequisites

- Python 3.12+
- [Ollama](https://ollama.com) running locally with the Qwen model pulled:
  ```bash
  ollama pull qwen3.5:0.8b
  ```
- Docker (for containerised runs)
- `kubectl` + a Kubernetes cluster (for K8s deployment)

> **Model name**: the default is `qwen3.5:0.8b` with reasoning disabled (`ENABLE_REASONING=false`). Override via env vars if needed.

---

## Running locally

```bash
# 1. Clone and enter the project
cd mood-ai-agent

# 2. Create a virtual environment
python -m venv .venv && source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and edit the env file
cp .env.example .env   # adjust MODEL_NAME / OLLAMA_BASE_URL if needed

# 5. Start the server (auto-reload enabled)
python -m src.main
# Or with more logs
LOG_LEVEL=DEBUG AGENT_VERBOSE=true python -m src.main
```

The API is available at `http://localhost:8000`.

### Quick test

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "I had the most amazing day, everything went perfectly!"}'
```

---

## API reference

| Method | Path       | Description                        |
|--------|------------|------------------------------------|
| GET    | `/health`  | Liveness check                     |
| POST   | `/analyze` | Evaluate mood from a text input    |

### POST /analyze

**Request body**
```json
{ "text": "I feel completely lost and overwhelmed today." }
```

**Response**
```json
{
  "input": "I feel completely lost and overwhelmed today.",
  "mood": "Person feels overwhelmed and lost, likely experiencing anxiety or sadness."
}
```

---

## Docker

```bash
# Build
docker build -t mood-agent:latest .

# Run (Ollama must be reachable from the container)
docker run -p 8000:8000 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  mood-agent:latest
```

---

## Kubernetes deployment

The `k8s/` folder contains all manifests:

| File                    | Purpose                                      |
|-------------------------|----------------------------------------------|
| `configmap.yaml`        | App environment variables                    |
| `deployment.yaml`       | Mood Agent deployment (2 replicas)           |
| `service.yaml`          | ClusterIP service on port 80                 |
| `ollama-deployment.yaml`| Ollama server + PVC + ClusterIP service      |

### Deploy

```bash
# 1. Push your image to a registry accessible by the cluster
docker tag mood-agent:latest <your-registry>/mood-agent:latest
docker push <your-registry>/mood-agent:latest

# Update the image field in k8s/deployment.yaml, then:

# 2. Apply manifests
kubectl apply -f k8s/ollama-deployment.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# 3. Pull the model inside the running Ollama pod
  kubectl exec -it deploy/ollama -- ollama pull qwen3.5:0.8b

# 4. Verify
kubectl get pods
kubectl port-forward svc/mood-agent 8000:80
curl http://localhost:8000/health
```

---

## Configuration

All settings are controlled via environment variables (or `.env`):

| Variable               | Default                    | Description                                              |
|------------------------|----------------------------|----------------------------------------------------------|
| `MODEL_NAME`           | `qwen3.5:0.8b`             | Ollama model tag                                         |
| `OLLAMA_BASE_URL`      | `http://localhost:11434`   | Ollama server URL                                        |
| `ENABLE_REASONING`     | `false`                    | Qwen3 internal chain-of-thought (`ChatOllama.reasoning`) |
| `AGENT_VERBOSE`        | `false`                    | Print LangGraph node traversals to stdout                |
| `AGENT_MAX_ITERATIONS` | `10`                       | LangGraph `recursion_limit` (max graph steps)            |
| `APP_HOST`             | `0.0.0.0`                  | Bind address                                             |
| `APP_PORT`             | `8000`                     | Bind port                                                |
| `LOG_LEVEL`            | `info`                     | Log level — set to `debug` to trace raw Ollama HTTP calls|

### Debugging in LangChain v1

> `LANGCHAIN_VERBOSE` and `LANGCHAIN_DEBUG` no longer exist in LangChain v1.

| Goal | How |
|---|---|
| See agent graph steps | `AGENT_VERBOSE=true` |
| See raw HTTP calls to Ollama | `LOG_LEVEL=debug` |
| Full traces with prompts & tokens | Set `LANGCHAIN_TRACING_V2=true` + `LANGCHAIN_API_KEY` (free at [smith.langchain.com](https://smith.langchain.com)) |

---

## Project structure

```
mood-ai-agent/
├── src/
│   ├── __init__.py
│   ├── agent.py        # LangChain v1 agent (create_agent)
│   ├── config.py       # Pydantic settings
│   └── main.py         # FastAPI app + entry point
├── k8s/
│   ├── configmap.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ollama-deployment.yaml
├── .env.example
├── .dockerignore
├── Dockerfile
├── requirements.txt
└── README.md
```
