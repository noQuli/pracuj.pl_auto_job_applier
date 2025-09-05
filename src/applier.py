from pydantic import BaseModel, Field
from src.login_selenium import PracujLogin
from src.index_scrapper import ScraperManager
from src.logger import SingletonLogger
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from src.browser_use_applier import JobApplier
from typing import Optional
import multiprocessing

# --- Constants ---
FAST_APPLY_SELECTOR = ".quick-apply_s1i8itcr > a:nth-child(2)"
NORMAL_APPLY_SELECTOR = ".quick-apply_s47rwpe > div:nth-child(1) > a:nth-child(1)"
CONTINUE_BUTTON_SELECTOR = "button.ui-library_b14qiyz3:nth-child(1)"

logger = SingletonLogger().get_logger()


# --- Pydantic Models ---
class ApplierConfig(BaseModel):
    email: str
    password: str
    filtered_job_url: str
    username: str = "main"
    apply_with_ai: bool = True
    headless: bool = True
    browser: str = "firefox"
    model_name: Optional[str] = None
    base_url: Optional[str] = None
    provider: Optional[str] = None
    api_key: Optional[str] = None


# --- Classes ---
class ClickApply:
    """Handles clicking 'apply' buttons on a job application page."""

    def __init__(self, driver, wait):
        self.driver = driver
        self.wait = wait

    def _click_button(self, selector: str) -> bool:
        """Clicks a button specified by a CSS selector."""
        try:
            button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            logger.debug(f"Finded button with selector: {selector}")
            button.click()
            logger.debug(f"Clicked button with selector: {selector}")
            return True
        except TimeoutException:
            logger.debug(f"Button with selector {selector} not found or not clickable.")
            return False

    def _handle_fast_apply(self) -> bool:
        """Handles the fast apply process."""
        if self._click_button(FAST_APPLY_SELECTOR):
            logger.info("Clicked fast apply button.")
            return True
        return False

    def _handle_normal_apply(self) -> str | None:
        """Handles the normal apply process and returns the new URL if successful."""
        if self._click_button(NORMAL_APPLY_SELECTOR):
            logger.info("Clicked normal apply button, looking for continue button.")
            if self._click_button(CONTINUE_BUTTON_SELECTOR):
                logger.info("Clicked continue button.")
                return self._get_new_window_url()
        return None

    def _get_new_window_url(self) -> str | None:
        """Switches to a new window and returns its URL."""
        original_window = self.driver.current_window_handle
        try:
            self.wait.until(EC.number_of_windows_to_be(2))
            new_window_handle = [
                window
                for window in self.driver.window_handles
                if window != original_window
            ][0]
            self.driver.switch_to.window(new_window_handle)
            self.wait.until(EC.url_contains("https://"))
            new_url = self.driver.current_url
            logger.info(f"Switched to new tab with URL: {new_url}")
            return new_url
        except (TimeoutException, IndexError):
            logger.warning(
                "No new window opened after clicking continue or URL did not change."
            )
            self.driver.switch_to.window(original_window)
            return None

    def find_and_click_apply(self) -> str | None:
        """
        Finds and clicks the appropriate apply button.
        Returns the new URL if a normal application is started, otherwise None.
        """
        if self._handle_fast_apply():
            return None

        new_url = self._handle_normal_apply()
        if new_url:
            return new_url

        logger.warning("No apply buttons were found or could be clicked.")
        return None


class Applier:
    """Manages the overall job application process."""

    def __init__(self, config: ApplierConfig):
        self.config = config
        self.driver = None
        self.wait = None
        self.offers = None

    @property
    def initialize_logged_in_driver(self):
        """Initializes and returns a logged-in Selenium WebDriver instance."""
        if not self.driver:
            try:
                self.driver, self.wait = PracujLogin(
                    self.config.email,
                    self.config.password,
                    self.config.username,
                    self.config.headless,
                    self.config.browser,
                ).login()
                logger.debug("Driver initialized successfully!")
                return self.driver, self.wait
            except Exception as e:
                logger.error(f"Couldn't initialize driver: {e}")
                raise
        return self.driver, self.wait

    @property
    def get_offers(self):
        """Scrapes and returns a list of job offer URLs."""
        if not self.offers:
            try:
                self.offers = ScraperManager(self.config.filtered_job_url).run_scraper()
                logger.debug("Offers's urls succesfully scraped")
                return self.offers
            except Exception as e:
                logger.error(f"Couldnt scrape offers's urls: {e}")
                raise
        return self.offers

    def apply(self):
        """Main method to start the application process."""
        self.offers = self.get_offers
        self.driver, self.wait = self.initialize_logged_in_driver
        main_window = self.driver.current_window_handle

        external_job_urls = []
        for url in self.offers:
            self.driver.get(url)
            clicker = ClickApply(self.driver, self.wait)
            new_url = clicker.find_and_click_apply()
            if new_url:
                logger.info(f"Found external application URL: {new_url}")
                external_job_urls.append(new_url)
                self.driver.close()
                self.driver.switch_to.window(main_window)

        if external_job_urls and self.config.apply_with_ai:
            logger.info(f"Found {len(external_job_urls)} external job applications.")
            self.apply_with_browser_agent(external_job_urls)
        else:
            logger.info(
                "No external job applications found to process, or you didnt choose apply_with_ai"
            )

    def _apply_job_for_url(self, url: str):
        """Helper to apply job in separate process with error handling."""
        logger.info(f"Starting job application for URL: {url}")
        try:
            job_applier = JobApplier(
                username=self.config.username,
                initial_url=url,
                model_name=self.config.model_name,
                base_url=self.config.base_url,
                provider=self.config.provider,
                api_key=self.config.api_key,
            )
            job_applier.run()
            logger.info(f"Successfully finished application for URL: {url}")
        except Exception as e:
            logger.error(f"An error occurred while applying for {url}: {e}")

    def apply_with_browser_agent(self, external_job_urls: list[str]):
        num_processes = multiprocessing.cpu_count() - 1
        if num_processes < 1:
            num_processes = 1
        logger.debug(f"Starting multiprocessing with {num_processes} processes for job applications.")
        with multiprocessing.Pool(processes=num_processes) as pool:
            pool.map(self._apply_job_for_url, external_job_urls)
