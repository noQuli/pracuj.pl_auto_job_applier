from src.webdriver_init import WebDriverInit
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import pickle
import os
from typing import Optional, List, Dict, Any
from src.logger import SingletonLogger
import sys
import json
from pathlib import Path
from selenium.common.exceptions import StaleElementReferenceException

logger = SingletonLogger().get_logger()


class CookieManager:
    """Handles cookie operations for session persistence"""

    def __init__(self, username):
        self.username = username
        self.data_dir = Path(__file__).resolve().parent.parent / "data"
        self.cookies_dir = self.data_dir / "cookies"
        self.cookies_file_pkl = os.path.join(
            self.cookies_dir, f"{self.username}_pracuj_cookies.pkl"
        )
        self.cookies_file_json = os.path.join(
            self.cookies_dir, f"{self.username}_pracuj_cookies.json"
        )

    def save_cookies(self, cookies: List[Dict[str, Any]]) -> bool:
        """Save cookies to both pickle and JSON files."""
        if not os.path.isdir(self.cookies_dir):
            try:
                os.makedirs(self.cookies_dir)
            except Exception as e:
                logger.error(f"Failed to create directory for cookies: {e}")
                return False

        # Save to pickle file
        try:
            with open(self.cookies_file_pkl, "wb") as f:
                pickle.dump(cookies, f)
            logger.info(f"Cookies saved to {self.cookies_file_pkl}")
        except Exception as e:
            logger.error(f"Failed to save cookies to pickle file: {e}")
            return False

        # Save to JSON file
        try:
            with open(self.cookies_file_json, "w") as f:
                json.dump(cookies, f, indent=4)
            logger.info(f"Cookies saved to {self.cookies_file_json}")
        except TypeError as e:
            logger.error(f"Failed to serialize cookies to JSON: {e}")
        except Exception as e:
            logger.error(f"Failed to save cookies to JSON file: {e}")
            return False

        return True

    def load_cookies(self) -> Optional[List[Dict[str, Any]]]:
        """Load cookies from pickle file"""
        try:
            if os.path.exists(self.cookies_file_pkl):
                with open(self.cookies_file_pkl, "rb") as f:
                    cookies = pickle.load(f)
                logger.info(f"Cookies loaded from {self.cookies_file_pkl}")
                return cookies
            else:
                logger.info("No cookies file found")
                return None
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            return None


class PageNavigator:
    """Handles page navigation operations"""

    def __init__(self, driver, wait):
        self.driver = driver
        self.wait = wait

    def navigate_to(self, url: str):
        """Navigate to a specific URL"""
        try:
            self.driver.get(url.strip())
            logger.debug(f"Navigated to {url}")
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            raise


class LoginElementInteractor:
    """Handles interaction with login page elements"""

    def __init__(self, driver, wait):
        self.driver = driver
        self.wait = wait

    def cookie_accept_button(self):
        """Click the initial continue button"""
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.size-medium:nth-child(1)")))
            continue_button = self.wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button.size-medium:nth-child(1)")
                )
            )
            continue_button.click()
            logger.debug("Clicked cookie accept button")
        except Exception as e:
            logger.error(f"Couldnt click cookie accept button: {e}")
            raise

    def enter_email(self, email: str):
        """Enter email address"""
        try:
            self.wait.until(EC.presence_of_element_located((By.ID, "email")))
            email_field = self.wait.until(EC.element_to_be_clickable((By.ID, "email")))
            email_field.clear()
            email_field.send_keys(email)
            logger.debug(f"Entered email: {email}")
        except StaleElementReferenceException as e:
            return self.enter_email(email)

    def click_email_continue(self):
        """Click continue after entering email"""
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".WelcomeForm_welcomeForm__7jIv2 > button:nth-child(2)")))
            continue_button = self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        ".WelcomeForm_welcomeForm__7jIv2 > button:nth-child(2)",
                    )
                )
            )
            continue_button.click()
            logger.debug("Clicked email continue button")
        except Exception as e:
            logger.error(f"Couldnt click email continue button {e}")
            raise

    def enter_password(self, password: str):
        """Enter password"""
        try:
            self.wait.until(EC.presence_of_element_located((By.ID, "password")))
            password_field = self.wait.until(
                EC.element_to_be_clickable((By.ID, "password"))
            )
            password_field.clear()
            password_field.send_keys(password)
            logger.debug("Entered password")
        except Exception as e:
            logger.error(f"Couldnt enter password: {e}")
            raise

    def click_login_button(self):
        """Click the final login button"""
        try:
            login_button = self.wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button.ui-library_b14qiyz3")
                )
            )
            login_button.click()
            logger.debug("Clicked login button")
        except Exception as e:
            logger.error(f"Couldnt click the final login button: {e}")
            raise


class PracujLogin:
    """Handles login functionality for Pracuj.pl with cookie-based auto-login"""

    def __init__(
        self,
        email: str,
        password: str,
        username: str = "main",
        headless: bool = True,
        browser: str = "firefox",
    ):
        self.headless = headless
        self.account_url = "https://www.pracuj.pl/konto"
        self.login_url = "https://login.pracuj.pl"
        self.email = email
        self.password = password
        self.username = username
        self.browser = browser

        if self.browser == "firefox":
            self.driver, self.wait = WebDriverInit(
                self.headless
            ).create_firefox_driver()
        elif self.browser == "chrome":
            self.driver, self.wait = WebDriverInit(self.headless).create_chrome_driver()
        self.cookie_manager = CookieManager(self.username)
        self.navigator = PageNavigator(self.driver, self.wait)
        self.element_interactor = LoginElementInteractor(self.driver, self.wait)

    def is_logged_in(self) -> bool:
        """
        Checks if the user is currently logged in by comparing the current URL
        with the expected account URL.
        """
        try:
            current_url = self.driver.current_url
            logger.debug(f"{current_url}")
            if current_url == self.account_url:
                logger.info(f"User is logged in.")
                return True
            logger.info(f"User is not logged in.")
            return False
        except Exception as e:
            logger.error(f"Error checking if logged in: {e}")
            return False

    def _apply_cookies(self, cookies: List[Dict[str, Any]]) -> None:
        """Apply cookies to the current session"""
        self.navigator.navigate_to(self.login_url)

        for cookie in cookies:
            try:
                self.driver.add_cookie(cookie)
            except Exception as e:
                logger.debug(
                    f"Could not add cookie {cookie.get('name', 'unknown')}: {e}"
                )

    def _perform_full_login_sequence(self):
        """Execute the complete login sequence"""
        try:
            self.navigator.navigate_to(self.login_url)
            self.element_interactor.cookie_accept_button()
            self.element_interactor.enter_email(self.email)
            self.element_interactor.click_email_continue()
            self.element_interactor.enter_password(self.password)
            self.element_interactor.click_login_button()
            self.wait.until(EC.url_contains("https://www.pracuj.pl/konto"))
            logger.info("Performed full login sequence")
        except Exception as e:
            logger.error(f"Couldnt perform full login sequence: {e}")
            raise

    def login(self):
        try:
            cookies = self.cookie_manager.load_cookies()
            if cookies:
                self._apply_cookies(cookies)
                self.navigator.navigate_to(self.account_url)
                # Wait for a moment to let the page load and verify login status
                try:
                    self.wait.until(EC.url_to_be(self.account_url))
                    if self.is_logged_in():
                        logger.info("Successfully logged in using cookies.")
                        return self.driver, self.wait
                except Exception:
                    logger.info("Cookie login failed, attempting full login.")

            if not (self.email and self.password):
                logger.error("Credentials were not provided and cookie login failed.")
                sys.exit()

            self._perform_full_login_sequence()
            if self.is_logged_in():
                logger.info("Full login successful.")
                current_cookies = self.driver.get_cookies()
                if self.cookie_manager.save_cookies(current_cookies):
                    logger.debug("New cookies saved successfully.")
                else:
                    logger.warning("Failed to save new cookies.")
                return self.driver, self.wait
            else:
                logger.error("Full login sequence performed but not logged in.")
                raise Exception("Login failed after full sequence.")

        except Exception as e:
            logger.error(f"Login failed: {e}")
            self.quit()
            raise

    def quit(self):
        if self.driver:
            self.driver.quit()
