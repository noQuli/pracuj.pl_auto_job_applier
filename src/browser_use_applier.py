from pathlib import Path

from dotenv import load_dotenv
from PyPDF2 import PdfReader 

from browser_use import (
    ActionResult,
    Agent,
    ChatOpenAI,
    Tools,
    ChatAnthropic,
    ChatAzureOpenAI,
    ChatGoogle,
    ChatGroq,
    ChatOllama,
)
from browser_use.browser import BrowserSession
from browser_use.browser.events import UploadFileEvent
from src.logger import SingletonLogger

load_dotenv()


logger = SingletonLogger().get_logger()

BASE_DIR = Path(__file__).resolve().parent.parent
CV_PATH = BASE_DIR / "data" / "CV"


class JobApplier:
    """
    A class to automate job applications using a browser agent.
    """

    def __init__(
        self,
        *,
        username: str,
        initial_url: str,
        model_name: str,
        provider: str,
        api_key: str,
        base_url: str,
    ):
        """
        Initializes the JobApplier.

        Args:
            username (str): The username for the user, used to construct the CV filename.
            initial_url (str): The URL of the job application page.
            model_name (str): The name of the language model to use.
            api_key (str): The API key for the language model.
            base_url (str): The base URL for the language model API.
        """
        self.username = username
        self.initial_url = initial_url
        self.model_name = model_name
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url
        self.cv_path = CV_PATH
        self.tools = self._register_tools()

    def load_cv(self) -> str:
        """
        Loads a CV from the given path and returns its text content.
        The path is expected to be a directory, and the filename is constructed using the username.
        """
        full_path = self.cv_path / f"{self.username}.pdf"
        logger.info(f"Attempting to load CV from {full_path}")
        try:
            pdf = PdfReader(full_path)
            text = "".join(page.extract_text() or "" for page in pdf.pages)
            logger.info(f"Loaded CV with {len(text)} characters")
            return text
        except FileNotFoundError:
            logger.error(f"CV file not found: {full_path}")
            return ""
        except Exception as e:
            logger.error(f"Error reading CV at {full_path}: {e}")
            return ""

    def _register_tools(self) -> Tools:
        """Registers the tools for the browser agent."""
        tools = Tools()

        @tools.action("Read my cv for context to fill forms")
        def read_cv():
            """Reads the user's CV and returns its text content."""
            text = self.load_cv()
            if not text:
                return ActionResult(
                    error=f"Could not load CV for username {self.username} from {self.cv_path}"
                )

            return ActionResult(extracted_content=text, include_in_memory=True)

        @tools.action(
            "Upload cv to element - call this function to upload if element is not found, try with different index of the same upload element",
        )
        async def upload_cv(index: int, browser_session: BrowserSession):
            """Uploads the CV to a file input element on the web page."""
            path = str((self.cv_path / f"{self.username}.pdf").absolute())

            dom_element = await browser_session.get_element_by_index(index)

            if dom_element is None:
                logger.info(f"No element found at index {index}")
                return ActionResult(error=f"No element found at index {index}")

            if not browser_session.is_file_input(dom_element):
                logger.info(f"Element at index {index} is not a file upload element")
                return ActionResult(
                    error=f"Element at index {index} is not a file upload element"
                )

            try:
                event = browser_session.event_bus.dispatch(
                    UploadFileEvent(node=dom_element, file_path=path)
                )
                await event
                await event.event_result(raise_if_any=True, raise_if_none=False)
                msg = f'Successfully uploaded file "{path}" to index {index}'
                logger.info(msg)
                return ActionResult(extracted_content=msg)
            except Exception as e:
                logger.debug(f"Error in upload: {str(e)}")
                return ActionResult(error=f"Failed to upload file to index {index}")

        return tools

    def construct_proper_model_call(self):
        provider_map = {
            "OpenAI": ChatOpenAI,
            "Anthropic": ChatAnthropic,
            "AzureOpenAI": ChatAzureOpenAI,
            "Google": ChatGoogle,
            "Groq": ChatGroq,
            "Ollama": ChatOllama,
            "OpenAI_compatible": ChatOpenAI,
        }

        try:
            model_class = provider_map[self.provider]
            if self.provider == "OpenAI_compatible":
                model = model_class(
                    model=self.model_name, base_url=self.base_url, api_key=self.api_key
                )
                return model
            model = model_class(model=self.model_name)
            return model
        except KeyError:
            raise ValueError(f"Unsupported provider: {self.provider}")

    async def run(self):
        """Runs the job application agent."""
        browser_session = BrowserSession(headless=False)

        initial_actions = [{"go_to_url": {"url": self.initial_url}}]
        ground_task = (
            "You are a professional job applier. "
            "On the current url, find how to apply. "
            "1. Read my cv with read_cv. "
            "2. Fill the form based on the CV."
            "Important: If you dont have info to fill something you can just make it up"
        )

        model = self.construct_proper_model_call()

        agent = Agent(
            task=ground_task,
            llm=model,
            tools=self.tools,
            browser_session=browser_session,
            initial_actions=initial_actions,
        )

        await agent.run()
