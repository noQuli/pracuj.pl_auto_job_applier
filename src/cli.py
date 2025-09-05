import questionary
from typing import Dict
from src.applier import ApplierConfig
import json
from pathlib import Path
from src.filter_url import get_filtered_pracuj_url
from src.logger import SingletonLogger
import sys


logger = SingletonLogger().get_logger()

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "data" / "config" / "configs.json"


def load_all_configs(filepath: Path) -> Dict[str, ApplierConfig]:
    """Loads all configurations from a JSON file."""
    if not filepath.exists():
        return {}
    with open(filepath, "r") as f:
        try:
            configs_dict = json.load(f)
            return {
                username: ApplierConfig(**config_data)
                for username, config_data in configs_dict.items()
            }
        except json.JSONDecodeError:
            return {}


def save_config_for_user(username: str, config: ApplierConfig, filepath: Path):
    """Saves a configuration for a specific user in the JSON file."""
    configs = load_all_configs(filepath)
    configs[username] = config

    configs_to_save = {user: conf.model_dump() for user, conf in configs.items()}

    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(configs_to_save, f, indent=4)


def collect_config_interactive() -> ApplierConfig:
    """Interactively collects configuration from the user."""
    configs = load_all_configs(CONFIG_FILE)

    if configs:
        action = questionary.select(
            "What would you like to do?",
            choices=[
                "Run with existing config",
                "Add new config",
                "Choose another filters for job",
                "Show config",
                "EXIT",
            ],
        ).ask()

        if action == "Run with existing config":
            username_to_run = questionary.select(
                "Which user config to run?", choices=list(configs.keys())
            ).ask()
            return configs[username_to_run]
        elif action == "Choose another filters for job":
            username_to_run = questionary.select(
                "Which user config to change filtered job?",
                choices=list(configs.keys()),
            ).ask()
            print("\n--- ATTENTION ---")
            print(
                "Please manually apply the desired filters on the page that just opened."
            )
            print("After selecting your filters, click the 'Wyszukaj' (Find) button.")
            print(
                "The script will automatically detect when the page reloads with new results."
            )
            print("Waiting for the URL to change (max 60 seconds)...")
            filtered_job_url = get_filtered_pracuj_url(
                browser=configs[username_to_run].browser
            )
            if filtered_job_url:
                config_to_update = configs[username_to_run]
                config_to_update.filtered_job_url = filtered_job_url
                save_config_for_user(username_to_run, config_to_update, CONFIG_FILE)
                logger.info(
                    f"Filtered URL for '{username_to_run}' updated in '{CONFIG_FILE}'."
                )
                return config_to_update
            else:
                logger.error("Could not get the filtered URL. No changes were made.")
                # Fall through to creating a new config
                return configs[username_to_run]
        elif action == "Show config":
            username_to_run = questionary.select(
                "Which user config you want to see?", choices=list(configs.keys())
            ).ask()
            print(json.dumps(configs[username_to_run].model_dump(), indent=4))
            sys.exit()
        elif action == "EXIT":
            sys.exit()

    print("🔧 New Configuration Setup")
    print("=" * 50)

    username = questionary.text("Enter username:").ask()
    email = questionary.text("Enter email:").ask()
    password = questionary.text("Enter password:").ask()
    apply_with_ai = questionary.confirm("Apply all offers", default=True).ask()
    headless = questionary.confirm("Run in headless mode?", default=True).ask()
    browser = questionary.select(
        "Select browser:", choices=["firefox", "chrome"], default="firefox"
    ).ask()
    
    model_name, provider, base_url, api_key = None , None , None , None 

    if apply_with_ai:
        model_name = questionary.text("Enter model name:").ask()
        provider = questionary.select(
            "Select provider:",
            choices=[
                "OpenAI",
                "Anthropic",
                "Google",
                "Groq",
                "AzureOpenAI",
                "Ollama",
                "OpenAI_compatible",
            ],).ask()

        if provider == "OpenAI_compatible":
            base_url = questionary.text(
                "Enter base URL (required for OpenAI compatible):"
            ).ask()
            api_key = questionary.text(
                "Enter API key (required for OpenAI compatible):"
            ).ask()

    print("\n--- ATTENTION ---")
    print("Please manually apply the desired filters on the page that just opened.")
    print("After selecting your filters, click the 'Wyszukaj' (Find) button.")
    print(
        "The script will automatically detect when the page reloads with new results."
    )
    print("Waiting for the URL to change (max 60 seconds)...")

    filtered_job_url = get_filtered_pracuj_url(browser=browser)

    new_config = ApplierConfig(
        email=email,
        password=password,
        filtered_job_url=filtered_job_url,
        username=username,
        apply_with_ai=apply_with_ai,
        headless=headless,
        browser=browser,
        model_name=model_name,
        base_url=base_url,
        provider=provider,
        api_key=api_key,
    )

    save_config_for_user(username, new_config, CONFIG_FILE)
    logger.info(f"Configuration for '{username}' saved to '{CONFIG_FILE}'.")

    return new_config


if __name__ == "__main__":
    config = collect_config_interactive()
    logger.debug("\nConfiguration loaded successfully:")
    print(config)
