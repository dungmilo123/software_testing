"""WebDriver factory. Selenium 4 resolves the matching chromedriver/geckodriver itself (Selenium Manager)."""
from selenium import webdriver

from common import config


def make_driver():
    if config.BROWSER == "firefox":
        opts = webdriver.FirefoxOptions()
        if config.HEADLESS:
            opts.add_argument("-headless")
        driver = webdriver.Firefox(options=opts)
        driver.set_window_size(1400, 1000)
    else:
        opts = webdriver.ChromeOptions()
        if config.CHROME_BINARY:  # another Chromium browser, e.g. CHROME_BINARY=/usr/bin/brave
            opts.binary_location = config.CHROME_BINARY
        if config.HEADLESS:
            opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1400,1000")
        opts.add_argument("--disable-search-engine-choice-screen")
        opts.add_experimental_option("prefs", {"credentials_enable_service": False,
                                               "profile.password_manager_enabled": False,
                                               "profile.password_manager_leak_detection": False})
        driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(120)
    return driver
