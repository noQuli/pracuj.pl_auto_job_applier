from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from src.webdriver_init import WebDriverInit
from src.logger import SingletonLogger

logger = SingletonLogger().get_logger()


def get_filtered_pracuj_url(browser: str = "firefox"):
    """
    Opens pracuj.pl, waits for user to apply filters and click search,
    then automatically detects the URL change and returns the new URL.
    """
    headless = False
    try:
        if browser == "firefox":
            driver, wait = WebDriverInit(headless).create_firefox_driver()
        elif browser == "chrome":
            driver, wait = WebDriverInit(headless).create_chrome_driver()

        # Open the initial URL
        logger.debug("Opening https://pracuj.pl/praca in your browser...")
        driver.get("https://pracuj.pl/praca")

        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        initial_url = driver.current_url

        wait.until(EC.url_changes(initial_url))
        logger.debug("URL has changed. Capturing the new URL...")

        # Get the current URL from the browser
        new_url = driver.current_url
        logger.debug(f"\nSuccessfully captured the new URL: {new_url}")
        return new_url

    except Exception as e:
        logger.debug(f"An error occurred: {e}")
        return None
    finally:
        # Close the browser window
        if driver:
            logger.debug("Closing the browser.")
            driver.quit()
