"""Base unittest class.

Keeps the structure of the code Katalon Recorder exports as "Python 2 (WebDriver + unittest)"
(setUp / tearDown, ``verificationErrors`` collected by soft ``verify*`` checks and asserted in tearDown),
ported to Python 3 and Selenium 4. One browser is opened per test class and logged in once; every test
case then runs in that session.
"""
import unittest

from selenium.common.exceptions import WebDriverException

from common import config
from common.data import describe
from common.driver import make_driver
from common.moodle import Moodle, norm


class MoodleTestCase(unittest.TestCase):
    login_user = None      # None = admin from config
    login_password = None
    login_at_start = True
    base_url = None        # None = MOODLE_BASE_URL from config

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        cls.m = Moodle(cls.driver, cls.base_url)
        if cls.login_at_start:
            cls.m.login(cls.login_user, cls.login_password)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def setUp(self):
        self.verificationErrors = []
        self.maxDiff = None

    def tearDown(self):
        self.assertEqual([], self.verificationErrors)

    # ---------------------------------------------------------------- soft checks (Katalon "verify*")
    def verify(self, condition, message):
        if not condition:
            self.verificationErrors.append(message)
        return condition

    def verify_equal(self, expected, actual, what):
        return self.verify(expected == actual, "%s: expected %s, got %s" % (what, describe(expected), describe(actual)))

    def verify_text(self, locator, expected, what=None):
        try:
            actual = self.m.text(locator, timeout=5)
        except WebDriverException:
            return self.verify(False, "%s: element %s not found (expected text %s)"
                               % (what or locator, locator, describe(expected)))
        return self.verify_equal(norm(expected), actual, what or locator)

    def verify_contains(self, locator, expected, what=None):
        try:
            actual = self.m.text(locator, timeout=5)
        except WebDriverException:
            return self.verify(False, "%s: element %s not found" % (what or locator, locator))
        return self.verify(norm(expected) in actual, "%s: %s not found in %s" % (what or locator, describe(expected), describe(actual, 120)))

    def verify_present(self, locator, what=None):
        try:
            self.m.wait(locator, timeout=5)
            return True
        except WebDriverException:
            return self.verify(False, "%s: element not present (%s)" % (what or "element", locator))

    def verify_not_present(self, locator, what=None):
        return self.verify(not self.m.exists(locator), "%s: element should not be present (%s)" % (what or "element", locator))

    def verify_value(self, locator, expected, what=None):
        try:
            actual = self.m.value(locator)
        except WebDriverException:
            return self.verify(False, "%s: field %s not found" % (what or locator, locator))
        return self.verify_equal(expected, actual, what or locator)

    def verify_field_error(self, field, expected):
        """expected '' means: no error may be shown under the field."""
        return self.verify_equal(norm(expected), self.m.field_error(field), "error under '%s'" % field)
