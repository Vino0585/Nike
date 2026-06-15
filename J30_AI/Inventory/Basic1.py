import asyncio
import os
from pathlib import Path

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from openai import APIConnectionError


def load_env_file(env_path: Path) -> bool:
    """Load KEY=VALUE entries from .env into os.environ without overriding existing values."""
    if not env_path.exists():
        return False

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)

    return True


async def main():
    print("Hello from main function")
    from autogen_ext.models.openai import OpenAIChatCompletionClient

    env_loaded = load_env_file(Path(__file__).resolve().parents[1] / ".env")
    if env_loaded:
        print("Loaded settings from project .env")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing OPENAI_API_KEY. Export it in your shell instead of hardcoding secrets in source files."
        )

    openai_model_client = OpenAIChatCompletionClient(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        api_key=api_key,
    )
    assistant = AssistantAgent(name="Vino_Assistant", model_client=openai_model_client)

    try:
        await Console(assistant.run_stream(task="What is 25 * 8"))
    except APIConnectionError as exc:
        root_cause = str(exc.__cause__ or exc)
        if "CERTIFICATE_VERIFY_FAILED" in root_cause:
            print("\nSSL verification failed.")
            print("If you are on a corporate network with TLS inspection, trust your corporate root CA.")
            print("Set SSL_CERT_FILE (or REQUESTS_CA_BUNDLE) to a PEM bundle containing that CA.")
            print("Example: export SSL_CERT_FILE=/path/to/corporate-ca.pem")
        raise
    finally:
        await openai_model_client.close()


if __name__ == "__main__":
    asyncio.run(main())
