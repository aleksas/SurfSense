import os
import shutil
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence
from urllib import error, request

import numpy as np
import yaml
from chonkie import AutoEmbeddings, CodeChunker, RecursiveChunker
from dotenv import load_dotenv
from rerankers import Reranker

# Get the base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env_file = BASE_DIR / ".env"
load_dotenv(env_file)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class OllamaEmbeddings:
    """Minimal embedding adapter for Ollama's /api/embed endpoint."""

    def __init__(
        self,
        model: str,
        api_base: str = "http://ollama:11434",
        timeout: float = 180.0,
        max_seq_length: int = 512,
        num_gpu: int | None = None,
    ):
        self.model = model
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout
        self.max_seq_length = max_seq_length
        self.num_gpu = num_gpu
        self.dimension = len(self.embed("ping"))

    def _embed_request(self, inputs: Sequence[str]) -> list[list[float]]:
        def _make_request(num_gpu_value: int | None) -> dict[str, Any]:
            payload_dict: dict[str, Any] = {"model": self.model, "input": list(inputs)}
            if num_gpu_value is not None:
                payload_dict["options"] = {"num_gpu": num_gpu_value}
            payload = json.dumps(payload_dict).encode("utf-8")
            req = request.Request(
                f"{self.api_base}/api/embed",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with request.urlopen(req, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))

        try:
            data = _make_request(self.num_gpu)
        except error.HTTPError as e:
            # Some embedding models (e.g. multilingual-e5 on certain GPU setups)
            # return NaN with GPU offload. Retry once on CPU instead of failing.
            if self.num_gpu not in (None, 0):
                try:
                    error_body = e.read().decode("utf-8", errors="ignore")
                except Exception:
                    error_body = ""
                if "NaN" in error_body:
                    data = _make_request(0)
                else:
                    raise ValueError(
                        f"Ollama embedding request failed ({e.code}): {e.reason}"
                    ) from e
            else:
                raise ValueError(
                    f"Ollama embedding request failed ({e.code}): {e.reason}"
                ) from e
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(
                f"Ollama embedding request failed: {e}"
            ) from e

        embeddings = data.get("embeddings")
        if not embeddings:
            raise ValueError(f"Ollama returned no embeddings for model '{self.model}'")
        return embeddings

    def embed(self, text: str) -> np.ndarray:
        return np.asarray(self._embed_request([text])[0], dtype=np.float32)

    def embed_batch(self, texts: list[str]) -> list[np.ndarray]:
        if not texts:
            return []
        vectors = self._embed_request(texts)
        return [np.asarray(v, dtype=np.float32) for v in vectors]


class JinaV3SentenceTransformerEmbeddings:
    """Jina v3 embeddings via sentence-transformers with task-aware encoding."""

    def __init__(
        self,
        model_name: str = "jinaai/jina-embeddings-v3",
        device: str | None = None,
        max_seq_length: int = 512,
        query_task: str = "retrieval.query",
        passage_task: str = "retrieval.passage",
        normalize_embeddings: bool = True,
        trust_remote_code: bool = True,
    ):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise ValueError(
                "sentence-transformers is required for jinaai/jina-embeddings-v3"
            ) from e

        self.model_name = model_name
        self.query_task = query_task
        self.passage_task = passage_task
        self.normalize_embeddings = normalize_embeddings
        self.max_seq_length = max_seq_length
        self.device = device

        model_kwargs: dict[str, Any] = {"trust_remote_code": trust_remote_code}
        if device:
            model_kwargs["device"] = device

        self.model = SentenceTransformer(model_name, **model_kwargs)
        if max_seq_length > 0:
            self.model.max_seq_length = max_seq_length
        self.dimension = int(self.model.get_sentence_embedding_dimension())

    def _encode(self, texts: list[str], task: str) -> np.ndarray:
        encode_kwargs: dict[str, Any] = {
            "convert_to_numpy": True,
            "normalize_embeddings": self.normalize_embeddings,
            "task": task,
        }
        try:
            vectors = self.model.encode(texts, **encode_kwargs)
        except TypeError:
            # Safety fallback if a future model revision does not accept task.
            encode_kwargs.pop("task", None)
            vectors = self.model.encode(texts, **encode_kwargs)
        return np.asarray(vectors, dtype=np.float32)

    def embed(self, text: str) -> np.ndarray:
        return self._encode([text], task=self.passage_task)[0]

    def embed_batch(self, texts: list[str]) -> list[np.ndarray]:
        if not texts:
            return []
        vectors = self._encode(texts, task=self.passage_task)
        return [vectors[i] for i in range(len(vectors))]

    def embed_query(self, text: str) -> np.ndarray:
        return self._encode([text], task=self.query_task)[0]

    def embed_query_batch(self, texts: list[str]) -> list[np.ndarray]:
        if not texts:
            return []
        vectors = self._encode(texts, task=self.query_task)
        return [vectors[i] for i in range(len(vectors))]


@dataclass
class OllamaRerankResultItem:
    document: Any
    score: float
    rank: int


@dataclass
class OllamaRerankResults:
    results: list[OllamaRerankResultItem]


class OllamaReranker:
    """Adapter that mimics rerankers' rank() output using an Ollama model."""

    def __init__(
        self,
        model_name: str,
        api_base: str = "http://ollama:11434",
        timeout: float = 180.0,
        max_doc_chars: int = 6000,
        num_predict: int = 8,
        num_gpu: int | None = None,
    ):
        self.model_name = model_name
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout
        self.max_doc_chars = max_doc_chars
        self.num_predict = num_predict
        self.num_gpu = num_gpu

    def _post_json(self, path: str, payload_dict: dict[str, Any]) -> dict[str, Any]:
        payload = json.dumps(payload_dict).encode("utf-8")
        req = request.Request(
            f"{self.api_base}{path}",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def _parse_score(self, raw_text: str) -> float | None:
        match = re.search(r"-?\d+(?:\.\d+)?", raw_text)
        if not match:
            return None
        try:
            score = float(match.group(0))
        except ValueError:
            return None

        if 1.0 < score <= 100.0:
            score /= 100.0
        return float(max(0.0, min(1.0, score)))

    def _lexical_score(self, query: str, document_text: str) -> float:
        query_terms = set(re.findall(r"\w+", query.lower()))
        doc_terms = set(re.findall(r"\w+", document_text.lower()))
        if not query_terms or not doc_terms:
            return 0.0
        overlap = len(query_terms & doc_terms)
        denom = (len(query_terms) * len(doc_terms)) ** 0.5
        if denom == 0:
            return 0.0
        return float(max(0.0, min(1.0, overlap / denom)))

    def _score_with_generate(self, query: str, document_text: str) -> float:
        content = (document_text or "")[: self.max_doc_chars]
        prompt = (
            "Score document relevance to the query.\n"
            "Return only one number between 0 and 1.\n\n"
            f"Query:\n{query}\n\n"
            f"Document:\n{content}\n\n"
            "Score:"
        )

        payload: dict[str, Any] = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0,
                "num_predict": self.num_predict,
            },
        }
        if self.num_gpu is not None:
            payload["options"]["num_gpu"] = self.num_gpu

        try:
            data = self._post_json("/api/generate", payload)
        except Exception:
            return self._lexical_score(query, content)
        score = self._parse_score((data.get("response") or "").strip())
        if score is not None:
            return score
        return self._lexical_score(query, content)

    def _rank_via_endpoint(
        self, path: str, query: str, docs: list[Any]
    ) -> OllamaRerankResults | None:
        try:
            data = self._post_json(
                path,
                {
                    "model": self.model_name,
                    "query": query,
                    "documents": [doc.text for doc in docs],
                },
            )
        except error.HTTPError as e:
            if e.code == 404:
                return None
            raise

        ranked: list[tuple[int, float]] = []
        for item in data.get("results", []):
            index = item.get("index")
            score = item.get("score")
            if (
                isinstance(index, int)
                and 0 <= index < len(docs)
                and isinstance(score, (float, int))
            ):
                ranked.append((index, float(score)))

        if not ranked:
            return None

        ranked.sort(key=lambda pair: pair[1], reverse=True)
        return OllamaRerankResults(
            results=[
                OllamaRerankResultItem(
                    document=docs[index],
                    score=score,
                    rank=rank + 1,
                )
                for rank, (index, score) in enumerate(ranked)
            ]
        )

    def rank(self, query: str, docs: list[Any], **_: Any) -> OllamaRerankResults:
        # Prefer native rerank endpoints when available.
        for endpoint in ("/api/rerank", "/v1/rerank"):
            endpoint_results = self._rank_via_endpoint(endpoint, query, docs)
            if endpoint_results:
                return endpoint_results

        # Fallback path for Ollama versions without rerank endpoints.
        scores = [
            (i, self._score_with_generate(query, doc.text))
            for i, doc in enumerate(docs)
        ]
        scores.sort(key=lambda pair: pair[1], reverse=True)
        return OllamaRerankResults(
            results=[
                OllamaRerankResultItem(
                    document=docs[index],
                    score=score,
                    rank=rank + 1,
                )
                for rank, (index, score) in enumerate(scores)
            ]
        )


def is_ffmpeg_installed():
    """
    Check if ffmpeg is installed on the current system.

    Returns:
        bool: True if ffmpeg is installed, False otherwise.
    """
    return shutil.which("ffmpeg") is not None


def load_global_llm_configs():
    """
    Load global LLM configurations from YAML file.
    Falls back to example file if main file doesn't exist.

    Returns:
        list: List of global LLM config dictionaries, or empty list if file doesn't exist
    """
    # Try main config file first
    global_config_file = BASE_DIR / "app" / "config" / "global_llm_config.yaml"

    if not global_config_file.exists():
        # No global configs available
        return []

    try:
        with open(global_config_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("global_llm_configs", [])
    except Exception as e:
        print(f"Warning: Failed to load global LLM configs: {e}")
        return []


def load_router_settings():
    """
    Load router settings for Auto mode from YAML file.
    Falls back to default settings if not found.

    Returns:
        dict: Router settings dictionary
    """
    # Default router settings
    default_settings = {
        "routing_strategy": "usage-based-routing",
        "num_retries": 3,
        "allowed_fails": 3,
        "cooldown_time": 60,
    }

    # Try main config file first
    global_config_file = BASE_DIR / "app" / "config" / "global_llm_config.yaml"

    if not global_config_file.exists():
        return default_settings

    try:
        with open(global_config_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            settings = data.get("router_settings", {})
            # Merge with defaults
            return {**default_settings, **settings}
    except Exception as e:
        print(f"Warning: Failed to load router settings: {e}")
        return default_settings


def load_global_image_gen_configs():
    """
    Load global image generation configurations from YAML file.

    Returns:
        list: List of global image generation config dictionaries, or empty list
    """
    global_config_file = BASE_DIR / "app" / "config" / "global_llm_config.yaml"

    if not global_config_file.exists():
        return []

    try:
        with open(global_config_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("global_image_generation_configs", [])
    except Exception as e:
        print(f"Warning: Failed to load global image generation configs: {e}")
        return []


def load_image_gen_router_settings():
    """
    Load router settings for image generation Auto mode from YAML file.

    Returns:
        dict: Router settings dictionary
    """
    default_settings = {
        "routing_strategy": "usage-based-routing",
        "num_retries": 3,
        "allowed_fails": 3,
        "cooldown_time": 60,
    }

    global_config_file = BASE_DIR / "app" / "config" / "global_llm_config.yaml"

    if not global_config_file.exists():
        return default_settings

    try:
        with open(global_config_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            settings = data.get("image_generation_router_settings", {})
            return {**default_settings, **settings}
    except Exception as e:
        print(f"Warning: Failed to load image generation router settings: {e}")
        return default_settings


def initialize_llm_router():
    """
    Initialize the LLM Router service for Auto mode.
    This should be called during application startup.
    """
    global_configs = load_global_llm_configs()
    router_settings = load_router_settings()

    if not global_configs:
        print("Info: No global LLM configs found, Auto mode will not be available")
        return

    try:
        from app.services.llm_router_service import LLMRouterService

        LLMRouterService.initialize(global_configs, router_settings)
        print(
            f"Info: LLM Router initialized with {len(global_configs)} models "
            f"(strategy: {router_settings.get('routing_strategy', 'usage-based-routing')})"
        )
    except Exception as e:
        print(f"Warning: Failed to initialize LLM Router: {e}")


def initialize_image_gen_router():
    """
    Initialize the Image Generation Router service for Auto mode.
    This should be called during application startup.
    """
    image_gen_configs = load_global_image_gen_configs()
    router_settings = load_image_gen_router_settings()

    if not image_gen_configs:
        print(
            "Info: No global image generation configs found, "
            "Image Generation Auto mode will not be available"
        )
        return

    try:
        from app.services.image_gen_router_service import ImageGenRouterService

        ImageGenRouterService.initialize(image_gen_configs, router_settings)
        print(
            f"Info: Image Generation Router initialized with {len(image_gen_configs)} models "
            f"(strategy: {router_settings.get('routing_strategy', 'usage-based-routing')})"
        )
    except Exception as e:
        print(f"Warning: Failed to initialize Image Generation Router: {e}")


class Config:
    # Check if ffmpeg is installed
    if not is_ffmpeg_installed():
        import static_ffmpeg

        # ffmpeg installed on first call to add_paths(), threadsafe.
        static_ffmpeg.add_paths()
        # check if ffmpeg is installed again
        if not is_ffmpeg_installed():
            raise ValueError(
                "FFmpeg is not installed on the system. Please install it to use the Surfsense Podcaster."
            )

    # Deployment Mode (self-hosted or cloud)
    # self-hosted: Full access to local file system connectors (Obsidian, etc.)
    # cloud: Only cloud-based connectors available
    DEPLOYMENT_MODE = os.getenv("SURFSENSE_DEPLOYMENT_MODE", "self-hosted")

    @classmethod
    def is_self_hosted(cls) -> bool:
        """Check if running in self-hosted mode."""
        return cls.DEPLOYMENT_MODE == "self-hosted"

    @classmethod
    def is_cloud(cls) -> bool:
        """Check if running in cloud mode."""
        return cls.DEPLOYMENT_MODE == "cloud"

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL")

    NEXT_FRONTEND_URL = os.getenv("NEXT_FRONTEND_URL")
    # Backend URL to override the http to https in the OAuth redirect URI
    BACKEND_URL = os.getenv("BACKEND_URL")

    # Auth
    AUTH_TYPE = os.getenv("AUTH_TYPE")
    REGISTRATION_ENABLED = os.getenv("REGISTRATION_ENABLED", "TRUE").upper() == "TRUE"

    # Google OAuth
    GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")

    # Google Calendar redirect URI
    GOOGLE_CALENDAR_REDIRECT_URI = os.getenv("GOOGLE_CALENDAR_REDIRECT_URI")

    # Google Gmail redirect URI
    GOOGLE_GMAIL_REDIRECT_URI = os.getenv("GOOGLE_GMAIL_REDIRECT_URI")

    # Google Drive redirect URI
    GOOGLE_DRIVE_REDIRECT_URI = os.getenv("GOOGLE_DRIVE_REDIRECT_URI")

    # Airtable OAuth
    AIRTABLE_CLIENT_ID = os.getenv("AIRTABLE_CLIENT_ID")
    AIRTABLE_CLIENT_SECRET = os.getenv("AIRTABLE_CLIENT_SECRET")
    AIRTABLE_REDIRECT_URI = os.getenv("AIRTABLE_REDIRECT_URI")

    # Notion OAuth
    NOTION_CLIENT_ID = os.getenv("NOTION_CLIENT_ID")
    NOTION_CLIENT_SECRET = os.getenv("NOTION_CLIENT_SECRET")
    NOTION_REDIRECT_URI = os.getenv("NOTION_REDIRECT_URI")

    # Atlassian OAuth (shared for Jira and Confluence)
    ATLASSIAN_CLIENT_ID = os.getenv("ATLASSIAN_CLIENT_ID")
    ATLASSIAN_CLIENT_SECRET = os.getenv("ATLASSIAN_CLIENT_SECRET")
    JIRA_REDIRECT_URI = os.getenv("JIRA_REDIRECT_URI")
    CONFLUENCE_REDIRECT_URI = os.getenv("CONFLUENCE_REDIRECT_URI")

    # Linear OAuth
    LINEAR_CLIENT_ID = os.getenv("LINEAR_CLIENT_ID")
    LINEAR_CLIENT_SECRET = os.getenv("LINEAR_CLIENT_SECRET")
    LINEAR_REDIRECT_URI = os.getenv("LINEAR_REDIRECT_URI")

    # Slack OAuth
    SLACK_CLIENT_ID = os.getenv("SLACK_CLIENT_ID")
    SLACK_CLIENT_SECRET = os.getenv("SLACK_CLIENT_SECRET")
    SLACK_REDIRECT_URI = os.getenv("SLACK_REDIRECT_URI")

    # Discord OAuth
    DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
    DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
    DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")
    DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

    # Microsoft Teams OAuth
    TEAMS_CLIENT_ID = os.getenv("TEAMS_CLIENT_ID")
    TEAMS_CLIENT_SECRET = os.getenv("TEAMS_CLIENT_SECRET")
    TEAMS_REDIRECT_URI = os.getenv("TEAMS_REDIRECT_URI")

    # ClickUp OAuth
    CLICKUP_CLIENT_ID = os.getenv("CLICKUP_CLIENT_ID")
    CLICKUP_CLIENT_SECRET = os.getenv("CLICKUP_CLIENT_SECRET")
    CLICKUP_REDIRECT_URI = os.getenv("CLICKUP_REDIRECT_URI")

    # Composio Configuration (for managed OAuth integrations)
    # Get your API key from https://app.composio.dev
    COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY")
    COMPOSIO_ENABLED = os.getenv("COMPOSIO_ENABLED", "FALSE").upper() == "TRUE"
    COMPOSIO_REDIRECT_URI = os.getenv("COMPOSIO_REDIRECT_URI")

    # LLM instances are now managed per-user through the LLMConfig system
    # Legacy environment variables removed in favor of user-specific configurations

    # Global LLM Configurations (optional)
    # Load from global_llm_config.yaml if available
    # These can be used as default options for users
    GLOBAL_LLM_CONFIGS = load_global_llm_configs()

    # Router settings for Auto mode (LiteLLM Router load balancing)
    ROUTER_SETTINGS = load_router_settings()

    # Global Image Generation Configurations (optional)
    GLOBAL_IMAGE_GEN_CONFIGS = load_global_image_gen_configs()

    # Router settings for Image Generation Auto mode
    IMAGE_GEN_ROUTER_SETTINGS = load_image_gen_router_settings()

    # Chonkie Configuration | Edit this to your needs
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
    EMBEDDING_MODEL_FALLBACK = os.getenv(
        "EMBEDDING_MODEL_FALLBACK",
        "intfloat/multilingual-e5-large-instruct",
    )
    EMBEDDING_MODEL_EFFECTIVE = EMBEDDING_MODEL
    # Azure OpenAI credentials from environment variables
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")

    # Pass Azure credentials to embeddings when using Azure OpenAI
    embedding_kwargs = {}
    if AZURE_OPENAI_ENDPOINT:
        embedding_kwargs["azure_endpoint"] = AZURE_OPENAI_ENDPOINT
    if AZURE_OPENAI_API_KEY:
        embedding_kwargs["azure_api_key"] = AZURE_OPENAI_API_KEY

    if EMBEDDING_MODEL.startswith("ollama://"):
        ollama_model = EMBEDDING_MODEL.replace("ollama://", "", 1).strip()
        ollama_api_base = os.getenv("EMBEDDING_OLLAMA_API_BASE", "http://ollama:11434")
        try:
            ollama_timeout = float(os.getenv("EMBEDDING_OLLAMA_TIMEOUT", "180"))
        except ValueError:
            ollama_timeout = 180.0
        try:
            embedding_max_seq_length = int(os.getenv("EMBEDDING_MAX_SEQ_LENGTH", "512"))
        except ValueError:
            embedding_max_seq_length = 512
        default_num_gpu = ""
        raw_num_gpu = os.getenv("EMBEDDING_OLLAMA_NUM_GPU", default_num_gpu).strip()
        try:
            ollama_num_gpu = int(raw_num_gpu) if raw_num_gpu else None
        except ValueError:
            ollama_num_gpu = None

        embedding_model_instance = OllamaEmbeddings(
            model=ollama_model,
            api_base=ollama_api_base,
            timeout=ollama_timeout,
            max_seq_length=embedding_max_seq_length,
            num_gpu=ollama_num_gpu,
        )
        EMBEDDING_MODEL_EFFECTIVE = f"ollama://{ollama_model}"
    elif EMBEDDING_MODEL.strip().lower() in {
        "jina-embeddings-v3",
        "jinaai/jina-embeddings-v3",
    }:
        jina_model_name = "jinaai/jina-embeddings-v3"
        jina_device = os.getenv("EMBEDDING_DEVICE", "").strip() or None
        if jina_device is None:
            try:
                import torch

                jina_device = "cuda" if torch.cuda.is_available() else "cpu"
            except Exception:
                jina_device = "cpu"
        try:
            embedding_max_seq_length = int(os.getenv("EMBEDDING_MAX_SEQ_LENGTH", "512"))
        except ValueError:
            embedding_max_seq_length = 512

        embedding_model_instance = JinaV3SentenceTransformerEmbeddings(
            model_name=jina_model_name,
            device=jina_device,
            max_seq_length=embedding_max_seq_length,
            query_task=os.getenv("EMBEDDING_JINA_QUERY_TASK", "retrieval.query"),
            passage_task=os.getenv("EMBEDDING_JINA_PASSAGE_TASK", "retrieval.passage"),
            normalize_embeddings=_env_bool("EMBEDDING_JINA_NORMALIZE", True),
            trust_remote_code=_env_bool("EMBEDDING_JINA_TRUST_REMOTE_CODE", True),
        )
        EMBEDDING_MODEL_EFFECTIVE = jina_model_name
    else:
        embedding_model_instance = AutoEmbeddings.get_embeddings(
            EMBEDDING_MODEL_EFFECTIVE,
            **embedding_kwargs,
        )
    # Prefer GPU for embeddings when available (container must be started with GPU access).
    try:
        import torch

        if torch.cuda.is_available():
            st_model = getattr(embedding_model_instance, "model", None)
            if st_model is not None and hasattr(st_model, "to"):
                st_model.to("cuda")
    except Exception:
        pass
    chunker_instance = RecursiveChunker(
        chunk_size=getattr(embedding_model_instance, "max_seq_length", 512)
    )
    code_chunker_instance = CodeChunker(
        chunk_size=getattr(embedding_model_instance, "max_seq_length", 512)
    )

    # Reranker's Configuration | Pinecone, Cohere etc. Read more at https://github.com/AnswerDotAI/rerankers?tab=readme-ov-file#usage
    RERANKERS_ENABLED = os.getenv("RERANKERS_ENABLED", "FALSE").upper() == "TRUE"
    reranker_instance = None
    if RERANKERS_ENABLED:
        RERANKERS_MODEL_NAME = os.getenv("RERANKERS_MODEL_NAME")
        RERANKERS_MODEL_TYPE = os.getenv("RERANKERS_MODEL_TYPE")
        RERANKERS_OLLAMA_API_BASE = os.getenv(
            "RERANKERS_OLLAMA_API_BASE", "http://ollama:11434"
        )
        try:
            RERANKERS_OLLAMA_TIMEOUT = float(
                os.getenv("RERANKERS_OLLAMA_TIMEOUT", "180")
            )
        except ValueError:
            RERANKERS_OLLAMA_TIMEOUT = 180.0
        try:
            RERANKERS_OLLAMA_MAX_DOC_CHARS = int(
                os.getenv("RERANKERS_OLLAMA_MAX_DOC_CHARS", "6000")
            )
        except ValueError:
            RERANKERS_OLLAMA_MAX_DOC_CHARS = 6000
        try:
            RERANKERS_OLLAMA_NUM_PREDICT = int(
                os.getenv("RERANKERS_OLLAMA_NUM_PREDICT", "8")
            )
        except ValueError:
            RERANKERS_OLLAMA_NUM_PREDICT = 8
        raw_reranker_ollama_num_gpu = os.getenv("RERANKERS_OLLAMA_NUM_GPU", "").strip()
        try:
            RERANKERS_OLLAMA_NUM_GPU = (
                int(raw_reranker_ollama_num_gpu)
                if raw_reranker_ollama_num_gpu
                else None
            )
        except ValueError:
            RERANKERS_OLLAMA_NUM_GPU = None
        # Rerankers may download model artifacts; make this robust against races
        # between backend/worker/beat processes importing config at the same time.
        RERANKERS_CACHE_DIR = os.getenv("RERANKERS_CACHE_DIR", "/tmp/flashrank_cache")
        try:
            os.makedirs(RERANKERS_CACHE_DIR, exist_ok=True)
        except Exception:
            pass
        try:
            if (RERANKERS_MODEL_TYPE or "").lower() == "ollama":
                reranker_instance = OllamaReranker(
                    model_name=RERANKERS_MODEL_NAME,
                    api_base=RERANKERS_OLLAMA_API_BASE,
                    timeout=RERANKERS_OLLAMA_TIMEOUT,
                    max_doc_chars=RERANKERS_OLLAMA_MAX_DOC_CHARS,
                    num_predict=RERANKERS_OLLAMA_NUM_PREDICT,
                    num_gpu=RERANKERS_OLLAMA_NUM_GPU,
                )
            else:
                reranker_instance = Reranker(
                    model_name=RERANKERS_MODEL_NAME,
                    model_type=RERANKERS_MODEL_TYPE,
                    cache_dir=RERANKERS_CACHE_DIR,
                )
        except Exception as e:
            print(f"Warning: Failed to initialize reranker ({RERANKERS_MODEL_TYPE}): {e}")
            reranker_instance = None

    # OAuth JWT
    SECRET_KEY = os.getenv("SECRET_KEY")

    # JWT Token Lifetimes
    ACCESS_TOKEN_LIFETIME_SECONDS = int(
        os.getenv("ACCESS_TOKEN_LIFETIME_SECONDS", str(24 * 60 * 60))  # 1 day
    )
    REFRESH_TOKEN_LIFETIME_SECONDS = int(
        os.getenv("REFRESH_TOKEN_LIFETIME_SECONDS", str(14 * 24 * 60 * 60))  # 2 weeks
    )

    # ETL Service
    ETL_SERVICE = os.getenv("ETL_SERVICE")

    # Pages limit for ETL services (default to very high number for OSS unlimited usage)
    PAGES_LIMIT = int(os.getenv("PAGES_LIMIT", "999999999"))

    if ETL_SERVICE == "UNSTRUCTURED":
        # Unstructured API Key
        UNSTRUCTURED_API_KEY = os.getenv("UNSTRUCTURED_API_KEY")

    elif ETL_SERVICE == "LLAMACLOUD":
        # LlamaCloud API Key
        LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")

    # Residential Proxy Configuration (anonymous-proxies.net)
    # Used for web crawling and YouTube transcript fetching to avoid IP bans.
    RESIDENTIAL_PROXY_USERNAME = os.getenv("RESIDENTIAL_PROXY_USERNAME")
    RESIDENTIAL_PROXY_PASSWORD = os.getenv("RESIDENTIAL_PROXY_PASSWORD")
    RESIDENTIAL_PROXY_HOSTNAME = os.getenv("RESIDENTIAL_PROXY_HOSTNAME")
    RESIDENTIAL_PROXY_LOCATION = os.getenv("RESIDENTIAL_PROXY_LOCATION", "")
    RESIDENTIAL_PROXY_TYPE = int(os.getenv("RESIDENTIAL_PROXY_TYPE", "1"))

    # Litellm TTS Configuration
    TTS_SERVICE = os.getenv("TTS_SERVICE")
    TTS_SERVICE_API_BASE = os.getenv("TTS_SERVICE_API_BASE")
    TTS_SERVICE_API_KEY = os.getenv("TTS_SERVICE_API_KEY")

    # STT Configuration
    STT_SERVICE = os.getenv("STT_SERVICE")
    STT_SERVICE_API_BASE = os.getenv("STT_SERVICE_API_BASE")
    STT_SERVICE_API_KEY = os.getenv("STT_SERVICE_API_KEY")

    # Validation Checks
    # Check embedding dimension
    if (
        hasattr(embedding_model_instance, "dimension")
        and embedding_model_instance.dimension > 2000
    ):
        raise ValueError(
            f"Embedding dimension for Model: {EMBEDDING_MODEL_EFFECTIVE} "
            f"has {embedding_model_instance.dimension} dimensions, which "
            f"exceeds the maximum of 2000 allowed by PGVector."
        )

    @classmethod
    def get_settings(cls):
        """Get all settings as a dictionary."""
        return {
            key: value
            for key, value in cls.__dict__.items()
            if not key.startswith("_") and not callable(value)
        }


# Create a config instance
config = Config()
