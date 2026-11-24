"""Page helper for Moodle 5.1 used by all scripts.

Locators are written like Katalon Recorder targets so they can be copied from the Project #2 suites and
from the Level 2 element files:  id=..., name=..., css=..., xpath=..., link=..., or a bare //xpath.
"""
import re
import time

from selenium.common.exceptions import (ElementClickInterceptedException, NoSuchElementException,
                                        StaleElementReferenceException, TimeoutException,
                                        WebDriverException)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from common import config

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December"]


def by(locator):
    """Convert a Katalon-style locator string into a Selenium (By, value) pair."""
    if locator.startswith("//") or locator.startswith("(//"):
        return By.XPATH, locator
    kind, _, value = locator.partition("=")
    kinds = {"id": By.ID, "name": By.NAME, "css": By.CSS_SELECTOR, "xpath": By.XPATH,
             "link": By.LINK_TEXT, "partial": By.PARTIAL_LINK_TEXT}
    if kind not in kinds:
        raise ValueError("unsupported locator %r" % locator)
    return kinds[kind], value


def norm(text):
    """Whitespace-normalised text (what Katalon's verifyText compares)."""
    return re.sub(r"\s+", " ", text or "").strip()


class Moodle:
    def __init__(self, driver, base_url=None):
        self.d = driver
        self.base = (base_url or config.BASE_URL).rstrip("/")

    # ---------------------------------------------------------------- navigation / waiting
    def url(self, path):
        return path if path.startswith("http") else self.base + "/" + path.lstrip("/")

    def open(self, path):
        self.d.get(self.url(path))
        self.wait_ready()

    def wait_ready(self, timeout=None):
        WebDriverWait(self.d, timeout or config.WAIT).until(
            lambda d: d.execute_script("return document.readyState") == "complete")

    def wait(self, locator, timeout=None, visible=False):
        cond = EC.visibility_of_element_located if visible else EC.presence_of_element_located
        try:
            return WebDriverWait(self.d, timeout or config.WAIT).until(cond(by(locator)))
        except TimeoutException:
            raise NoSuchElementException("element not found: %s" % locator)

    def wait_gone(self, locator, timeout=None):
        WebDriverWait(self.d, timeout or config.WAIT).until(lambda d: not d.find_elements(*by(locator)))

    def find(self, locator, timeout=None):
        return self.wait(locator, timeout)

    def exists(self, locator):
        return len(self.d.find_elements(*by(locator))) > 0

    def visible(self, locator):
        return any(e.is_displayed() for e in self.d.find_elements(*by(locator)))

    def pause(self, ms):
        time.sleep(ms / 1000.0)

    # ---------------------------------------------------------------- actions
    def click(self, locator, timeout=None):
        el = WebDriverWait(self.d, timeout or config.WAIT).until(EC.element_to_be_clickable(by(locator)))
        self.d.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        try:
            el.click()
        except (ElementClickInterceptedException, StaleElementReferenceException):
            self.d.execute_script("arguments[0].click();", self.find(locator))

    def submit(self, locator, timeout=None):
        """Click a button that loads a new page and wait until the new page is ready."""
        old = self.d.find_element(By.TAG_NAME, "html")
        self.click(locator, timeout)
        t0 = time.time()

        def replaced(_):
            try:
                old.is_enabled()
            except WebDriverException:  # stale / node detached: the old page is gone
                return True
            # no navigation: Moodle's client-side validation shows the error under the field instead
            return time.time() - t0 > 1.5 and self.d.execute_script(
                "return [...document.querySelectorAll('.invalid-feedback')]"
                ".some(e => e.offsetParent && e.textContent.trim());")
        try:
            WebDriverWait(self.d, timeout or config.WAIT * 2).until(replaced)
        except TimeoutException:
            pass  # same-page action (client-side validation); caller verifies the outcome
        self.wait_ready()

    def type(self, locator, value, keyboard=False):
        """Replace the content of a text field.

        Like Katalon Recorder's ``type``, a value longer than the field's HTML maxlength is not cut by the
        browser: it is written with JavaScript so that the server-side validation is what gets tested.
        Long values (>200 chars) are also written with JavaScript to keep the run fast.
        keyboard=True always types key by key, so the browser applies maxlength like for a real user.
        """
        el = self.find(locator)
        maxlen = el.get_attribute("maxlength")
        too_long = maxlen and maxlen.isdigit() and len(value) > int(maxlen)
        if not keyboard and (too_long or len(value) > 200):
            self.d.execute_script(
                "arguments[0].value=arguments[1];"
                "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
                "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));", el, value)
            return
        self.d.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        el.clear()
        el.send_keys(Keys.CONTROL, "a")
        el.send_keys(Keys.DELETE)
        if value:
            el.send_keys(value)

    def select(self, locator, option):
        """Choose an option of a <select>: by visible label (default) or 'value=<v>'.

        Some Moodle 5.1 selects are hidden behind a custom chooser (e.g. Course format); like Katalon's
        ``select`` the option is then chosen on the hidden element and a change event is fired."""
        el = self.find(locator)
        if el.is_displayed():
            sel = Select(el)
            if option.startswith("value="):
                sel.select_by_value(option[6:])
            else:
                sel.select_by_visible_text(option)
            return
        found = self.d.execute_script(
            "var s=arguments[0], want=arguments[1], byValue=arguments[2];"
            "for (var o of s.options) {"
            "  var hit = byValue ? o.value===want : o.textContent.replace(/\\s+/g,' ').trim()===want;"
            "  if (hit) { s.value=o.value; s.dispatchEvent(new Event('change',{bubbles:true})); return true; } }"
            "return false;", el, option[6:] if option.startswith("value=") else option, option.startswith("value="))
        if not found:
            raise NoSuchElementException("option %r not found in %s" % (option, locator))

    def selected_label(self, locator):
        return norm(Select(self.find(locator)).first_selected_option.get_attribute("textContent"))

    def options(self, locator):
        return [o.get_attribute("value") for o in Select(self.find(locator)).options]

    def set_checkbox(self, locator, on):
        """Tick/untick with a real click (Moodle's disabledIf/hideIf rules listen to the click).
        A checkbox inside a collapsed section is set directly, like Katalon's ``check``."""
        el = self.find(locator)
        if el.is_selected() == on:
            return
        if el.is_displayed():
            self.click(locator)
        else:
            self.d.execute_script("arguments[0].checked=arguments[1];"
                                  "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));", el, on)

    def set_date(self, prefix, spec):
        """Fill a Moodle date selector.  prefix = 'id_startdate'; spec = 'off' | 'YYYY' | 'YYYY-MM-DD' |
        'YYYY-MM-DD HH:MM'.  The '<prefix>_enabled' checkbox (if any) is ticked, or unticked for 'off'."""
        enabled = "id=%s_enabled" % prefix
        if spec.lower() in ("off", "disabled", "no"):
            if self.exists(enabled):
                self.set_checkbox(enabled, False)
            return
        if self.exists(enabled):
            self.set_checkbox(enabled, True)
        m = re.match(r"^(\d{4})(?:-(\d{2})-(\d{2}))?(?:[ T](\d{2}):(\d{2}))?$", spec.strip())
        if not m:
            raise ValueError("bad date %r (use YYYY, YYYY-MM-DD or YYYY-MM-DD HH:MM)" % spec)
        year, month, day, hour, minute = m.groups()
        if day:
            self.select("id=%s_day" % prefix, str(int(day)))
            self.select("id=%s_month" % prefix, MONTHS[int(month) - 1])
        self.select("id=%s_year" % prefix, year)
        if hour is not None:
            self.select("id=%s_hour" % prefix, hour)
            self.select("id=%s_minute" % prefix, minute)

    def set_editor(self, textarea_id, html):
        """Set the content of a TinyMCE editor (falls back to the plain textarea)."""
        self.find("id=" + textarea_id)
        WebDriverWait(self.d, config.WAIT).until(lambda d: d.execute_script(
            "return !window.tinymce || !!tinymce.get(arguments[0]) || "
            "!document.getElementById(arguments[0]+'_ifr');", textarea_id))
        self.d.execute_script(
            "var id=arguments[0], v=arguments[1];"
            "var ed=window.tinymce && tinymce.get(id);"
            "if(ed){ed.setContent(v); ed.save(); ed.fire('change');}"
            "var t=document.getElementById(id); t.value=ed?ed.getContent():v;"
            "t.dispatchEvent(new Event('change',{bubbles:true}));", textarea_id, html)

    def editor_text(self, textarea_id):
        self.find("id=" + textarea_id)
        return norm(self.d.execute_script(
            "var ed=window.tinymce && tinymce.get(arguments[0]);"
            "if(ed){return ed.getBody().textContent;}"
            "var d=document.createElement('div'); d.innerHTML=document.getElementById(arguments[0]).value;"
            "return d.textContent;", textarea_id))

    def expand_all(self):
        """Open every collapsed section of a Moodle form ('Expand all')."""
        loc = "xpath=//a[contains(@class,'collapseexpand') and contains(normalize-space(.),'Expand all')]"
        if self.visible(loc):
            self.click(loc)
            WebDriverWait(self.d, config.WAIT).until(lambda d: not d.find_elements(
                By.CSS_SELECTOR, "fieldset.collapsible .fcontainer.collapsing"))
            time.sleep(0.4)

    # ---------------------------------------------------------------- reading the page
    def text(self, locator, timeout=None):
        return norm(self.find(locator, timeout).get_attribute("textContent"))

    def value(self, locator):
        return self.find(locator).get_attribute("value")

    def attribute(self, locator, name):
        return self.find(locator).get_attribute(name)

    def field_error(self, field):
        """Text of the validation message under a form field (id_error_<field>), '' when none is shown."""
        els = self.d.find_elements(By.ID, "id_error_" + field)
        return norm(els[0].get_attribute("textContent")) if els and els[0].is_displayed() else ""

    def page_text(self):
        return norm(self.d.find_element(By.TAG_NAME, "body").get_attribute("textContent"))

    def sesskey(self):
        return self.d.execute_script("return M.cfg.sesskey")

    # ---------------------------------------------------------------- session
    def login(self, user=None, password=None):
        """Log in through the login form. A brand-new browser session gets 'Invalid login' on its very
        first POST (session cookie not yet set), so the form is submitted a second time if needed."""
        user, password = user or config.ADMIN_USER, password or config.ADMIN_PASS
        for _ in range(2):
            self.open("/login/index.php")
            if not self.exists("id=username"):  # someone is already logged in
                self.logout()
                self.open("/login/index.php")
            self.type("id=username", user)
            self.type("id=password", password)
            self.submit("id=loginbtn")
            if "/login/index.php" not in self.d.current_url and self.exists("css=#user-menu-toggle"):
                return
        raise AssertionError("login failed for %s" % user)

    def logout(self):
        self.open("/login/logout.php?sesskey=" + self.sesskey())
        if self.exists("xpath=//form[contains(@action,'logout.php')]//button[@type='submit']"):
            self.submit("xpath=//form[contains(@action,'logout.php')]//button[@type='submit']")

    def dismiss_tour(self):
        if self.visible("css=button[data-role='end']"):
            self.click("css=button[data-role='end']")

    # ---------------------------------------------------------------- course data
    def course_id(self, shortname=config.COURSE_SHORTNAME):
        self.open("/course/view.php?name=" + shortname)
        m = re.search(r"\bcourse-(\d+)\b", self.d.find_element(By.TAG_NAME, "body").get_attribute("class"))
        if not m:
            raise AssertionError("course %s not found" % shortname)
        return int(m.group(1))

    def find_course_ids(self, search):
        """Ids of the courses listed by the course management search for `search`."""
        self.open("/course/management.php?search=" + search)
        ids = []
        for a in self.d.find_elements(By.XPATH, "//a[contains(@href,'/course/delete.php?id=')]"):
            ids.append(int(re.search(r"id=(\d+)", a.get_attribute("href")).group(1)))
        return ids

    def delete_course_by_id(self, course_id):
        self.open("/course/delete.php?id=%d" % course_id)
        self.submit("xpath=//form[contains(@action,'delete.php')]//button[@type='submit']")

    def delete_courses(self, search, keep=(config.COURSE_SHORTNAME,)):
        """Delete every course whose short/full name matches `search`, never the shared fixture course."""
        deleted = 0
        for cid in self.find_course_ids(search):
            self.open("/course/edit.php?id=%d" % cid)
            if self.value("id=id_shortname") in keep:
                continue
            self.delete_course_by_id(cid)
            deleted += 1
        return deleted

    def delete_activities(self, modname, shortname=config.COURSE_SHORTNAME):
        """Delete every activity of one type (quiz, assign, ...) from a course; returns how many."""
        self.open("/course/view.php?name=" + shortname)
        cmids = [int(e.get_attribute("id").split("-")[1]) for e in
                 self.d.find_elements(By.CSS_SELECTOR, "li.activity.modtype_%s[id^='module-']" % modname)]
        key = self.sesskey()
        for cmid in cmids:
            self.open("/course/mod.php?delete=%d&confirm=1&sesskey=%s" % (cmid, key))
        return len(cmids)
