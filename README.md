# Pracuj Autocv

A Python application to automate job applications on the pracuj.pl website.

On pracuj.pl, there are two types of job offers:
1.  **Fast Apply:** These offers can be applied to using the "Fast Apply" button. You only need to configure your information and add your CV to your pracuj.pl account.
2.  **Company Forms:** These offers redirect to the company's custom application form. This application uses an open-source browser automation utility to handle these.

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/pavel/pracuj_autocv
    cd pracuj_autocv
    ```

2.  Install dependencies using `uv`:
    ```bash
    uv sync
    ```

## Preparation

1.  Create an account on pracuj.pl with your email and password. Then, configure your profile at https://www.pracuj.pl/konto, adding your email, phone number, CV, and other relevant information.

2.  In the `data/CV` directory, add your CV in `.pdf` format. The name of the file should be the username you will use in the CLI.

3.  Rename the `.env.example` file to `.env` and add your API keys.

## Detailed Configuration

The `.env` file is used to store your API keys for the different AI providers. The following variables can be set:

```
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=
GOOGLE_API_KEY=
DEEPSEEK_API_KEY=
GROK_API_KEY=
```

## Usage

Run the `run_code.py` file to start the application.

```bash
uv run run_code.py
```

## Guide on Using the Application

1.  When you run the app, you will be prompted to provide a username. This username is used for storing your configuration and for using the correct CV. This allows for the use of multiple configurations.

2.  You will then have two options:
    *   Apply without AI (only for "Fast Apply" offers).
    *   Apply to all offers using AI.

3.  You can also choose to run the browser in headless mode (without a visible browser window). You can then choose which browser to use.

4.  If you choose to apply to all offers, you will need to select an AI provider. If you choose an OpenAI-compatible provider, you will need to provide your API key and the base URL for your provider.

5.  After you have provided all the necessary data, a browser tab will open. You should then choose the filters you want, such as location or job title, and then click "Find" (Wyszukaj).

6.  The next time you run the code, you can choose to run with an existing configuration or create a new one. You can also change the job filters for an existing configuration.

## Project structure 

*   **`data/`**: Contains user-specific data, such as configs, cookies, cover letters, and CVs.
*   **`src/`**: Contains the main source code for the application.
    *   **`applier.py`**: Contains the logic for applying to job offers.
    *   **`browser_use_applier.py`**: Contains the logic for applying to job offers using the browser automation utility.
    *   **`cli.py`**: Contains the command-line interface for the application.
    *   **`filter_url.py`**: Contains the logic for getting the filtered job URL.
    *   **`index_scrapper.py`**: Contains the logic for scrapping the job offers from the index page.
    *   **`logger.py`**: Contains the logging configuration.
    *   **`login_selenium.py`**: Contains the logic for logging in to the website.
    *   **`webdriver_init.py`**: Contains the logic for initializing the webdriver.
*   **`run_code.py`**: The main entry point for the application.

## Dependencies

The project's dependencies are listed in the `pyproject.toml` file and include:

*   pydantic
*   selenium
*   python-dotenv
*   PyPDF2
*   browser-use
*   questionary
*   requests
*   beautifulsoup4
*   fake-useragent

## Troubleshooting

*   **Login Issues:** If you are having trouble logging in, make sure your email and password are correct in your configuration. You can also try deleting the cookies for the website, which are stored in the `data/cookies` directory. Also config is stored in `data/config`
*   **Browser Automation Issues:** If the browser automation is not working as expected. You can also try running the application in non-headless mode to see what is happening in the browser.

## Contributing

Contributions are welcome! If you have a feature request, bug report, or want to contribute to the code, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.