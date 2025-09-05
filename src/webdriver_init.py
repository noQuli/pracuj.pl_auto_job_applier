from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver import Firefox
from selenium.webdriver import FirefoxOptions
from selenium.webdriver import Chrome
from selenium.webdriver import ChromeOptions
from fake_useragent import UserAgent
from selenium.webdriver import FirefoxProfile
from src.logger import SingletonLogger
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException

logger = SingletonLogger().get_logger()
ignored_exceptions=(NoSuchElementException,StaleElementReferenceException,)

class WebDriverInit:
    """creating WebDriver instance"""

    def __init__(self, headless):
        self.headless = headless

    @staticmethod
    def create_useragent():
        ua = UserAgent()
        useragent = ua.random
        return useragent

    def create_firefox_driver(self) -> tuple:
        """Create Firefox driver with appropriate options"""
        try:
            firefox_options = FirefoxOptions()
            firefox_profile = FirefoxProfile()
            if self.headless:
                firefox_options.add_argument("-headless")
            firefox_options.add_argument("--no-sandbox")
            firefox_options.add_argument("--disable-dev-shm-usage")
            firefox_profile.set_preference(
                "general.useragent.override", self.create_useragent()
            )
            firefox_profile.set_preference("dom.webdriver.enabled", False)
            firefox_profile.set_preference("useAutomationExtension", False)
            firefox_options.profile = firefox_profile
            driver = Firefox(options=firefox_options)
            wait = WebDriverWait(driver, 15)
            logger.info("Firefox driver initialized successfully")
            return driver, wait
        except Exception as e:
            logger.error(f"Failed to initialize Firefox driver: {e}")
            raise

    def create_chrome_driver(self) -> tuple:
        """Create Chrome driver with appropriate options"""
        try:
            chrome_options = ChromeOptions()
            if self.headless:
                chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument(f"--user-agent={self.create_useragent()}")
            driver = Chrome(options=chrome_options)
            wait = WebDriverWait(driver, 15, ignored_exceptions=ignored_exceptions)
            logger.info("Chrome driver initilized successfully")
            return driver, wait
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {e}")
            raise
