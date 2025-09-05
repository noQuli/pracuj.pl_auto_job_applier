import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import multiprocessing
from src.webdriver_init import WebDriverInit
from src.logger import SingletonLogger

logger = SingletonLogger().get_logger()


class PageNavigator:
    """Handles navigation and determination of the maximum page number for a given URL."""

    def __init__(self, base_url: str):
        self.base_url = base_url

    def get_max_page_number(self) -> int:
        """Determines the maximum page number from the initial URL."""
        headers = {"user-agent": WebDriverInit.create_useragent()}
        try:
            response = requests.get(self.base_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            max_page_element = soup.find(
                "span", {"data-test": "top-pagination-max-page-number"}
            )

            if max_page_element:
                max_page = int(max_page_element.text.strip())
                logger.debug(f"Max page number found: {max_page}")
                return max_page
            else:
                logger.debug(
                    "No explicit max page number element found. Assuming 1 page."
                )
                return 1

        except requests.exceptions.RequestException as req_err:
            logger.error(
                f"Request error for {self.base_url}: {req_err}", exc_debug=True
            )
            return 1
        except Exception as e:
            logger.error(
                f"An unexpected error occurred for {self.base_url}: {e}", exc_debug=True
            )
            return 1

    def generate_all_page_urls(self) -> list[str]:
        """Generates a list of all page URLs to be scraped."""
        num_of_pages = self.get_max_page_number()
        list_of_urls = [self.base_url]
        for page_num in range(2, num_of_pages + 1):
            if "?" in self.base_url:
                list_of_urls.append(f"{self.base_url}&pn={page_num}")
            else:
                list_of_urls.append(f"{self.base_url}?pn={page_num}")
        logger.debug(f"Generated {len(list_of_urls)} URLs for scraping.")
        return list_of_urls


class SeleniumScraper:
    """
    Scrapes URLs from a dynamic page using Selenium and BeautifulSoup.
    Handles clicking buttons to reveal more offers.
    """

    def __init__(self, headless: bool = True, browser: str = "firefox"):
        self.driver = None
        self.browser = browser
        self.headless = headless
        self.wait = None
        self._initialize_driver()

    def _initialize_driver(self):
        try:
            if self.browser == "firefox":
                self.driver, self.wait = WebDriverInit(
                    self.headless
                ).create_firefox_driver()
            elif self.browser == "chrome":
                self.driver, self.wait = WebDriverInit(
                    self.headless
                ).create_chrome_driver()
            logger.debug("Succesfully initialized webdriver")
        except Exception as e:
            logger.error(f"Couldnt initialized webdriver {e}")
            raise

    def _click_dynamic_buttons(self):
        """Attempts to find and click buttons that reveal more offers."""
        xpath_buttons = (
            "//div[@class='tiles_cobg3mp' and @tabindex='0' and @role='button']"
        )
        try:
            buttons = self.driver.find_elements(By.XPATH, xpath_buttons)
            if buttons:
                logger.debug(f"Found {len(buttons)} button(s) to click on the page.")
                for i, button in enumerate(buttons):
                    try:
                        self.driver.execute_script("arguments[0].click();", button)
                        logger.debug(
                            f"Clicked button {i+1}/{len(buttons)} using JavaScript."
                        )
                    except Exception as e:
                        logger.error(
                            f"Could not click button {i+1} due to another error: {e}"
                        )
            else:
                logger.debug("No dynamic buttons found based on the specified XPath.")
        except TimeoutException:
            logger.warning(
                "Timeout waiting for buttons. Proceeding to scrape without clicking."
            )
        except Exception as e:
            logger.error(f"An error occurred during button clicking phase: {e}")

    def scrape_urls(self, url: str) -> list[str]:
        """Navigates to a URL, interacts with the page, and scrapes target URLs."""
        scraped_urls = []
        try:
            self.driver.get(url)
            logger.debug(f"Navigated to: {url}")
            self._click_dynamic_buttons()

            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")
            target_links = soup.find_all(attrs={"data-test": "link-offer"})

            for link in target_links:
                href = link.get("href")
                if (
                    href and "boosterAI" not in href
                ):  # pracuj.pl has boosterai promotion, so promoted offers repeat twice if "boosterAI" not in href not set
                    scraped_urls.append(href)
            logger.info(f"Scraped {len(scraped_urls)} URLs from {url}.")

        except Exception as e:
            logger.error(f"An error occurred while scraping {url}: {e}")
        return scraped_urls

    def close_driver(self):
        """Closes the Selenium WebDriver."""
        if self.driver:
            self.driver.quit()
            logger.debug("Selenium WebDriver closed.")


class ScraperManager:
    """Manages the overall scraping process, including multiprocessing."""

    def __init__(self, base_url: str, headless: bool = True, browser: str = "firefox"):
        self.base_url = base_url
        self.page_navigator = PageNavigator(base_url)
        self.headless = headless
        self.browser = browser 

    def _scrape_single_page(self, url: str) -> list[str]:
        """Scrapes single page"""
        scraper = SeleniumScraper(headless=self.headless, browser=self.browser)
        try:
            return scraper.scrape_urls(url)
        finally:
            scraper.close_driver()  # Ensure driver is closed after each page's scraping in the pool

    def run_scraper(self) -> list[str]:
        """Executes the web scraping process using multiprocessing."""
        urls_to_scrape = self.page_navigator.generate_all_page_urls()
        scraped_data = []
        num_processes = multiprocessing.cpu_count() - 1
        if num_processes < 1:
            num_processes = 1
        logger.debug(f"Starting multiprocessing with {num_processes} processes.")
        with multiprocessing.Pool(processes=num_processes) as pool:
            for res in pool.imap_unordered(self._scrape_single_page, urls_to_scrape):
                scraped_data.extend(res)
        logger.info(f"Finished scraping. Total URLs collected: {len(scraped_data)}")
        return scraped_data


