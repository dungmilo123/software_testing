"""Feature-specific helpers for F001 Quiz Settings Level 2 flows."""
from selenium.webdriver.common.by import By

from common import config


def open_new_quiz(m):
    """Open the New Quiz settings form for KTC01 and expand all sections."""
    cid = m.course_id(config.COURSE_SHORTNAME)
    m.open("/course/modedit.php?add=quiz&type=&course=%d&section=0&return=0" % cid)
    expand_form_sections(m)


def expand_form_sections(m):
    """Expand all collapsible fieldsets and visible 'Show more...' toggles."""
    m.expand_all()
    for hdr in m.d.find_elements(By.CSS_SELECTOR, "fieldset.collapsible a.fheader.collapsed"):
        m.d.execute_script("arguments[0].scrollIntoView({block:'center'});", hdr)
        m.d.execute_script("arguments[0].click();", hdr)
    for toggler in m.d.find_elements(By.CSS_SELECTOR, "a.moreless-toggler"):
        if toggler.is_displayed() and "Show more" in (toggler.text or ""):
            m.d.execute_script("arguments[0].scrollIntoView({block:'center'});", toggler)
            m.d.execute_script("arguments[0].click();", toggler)
    m.pause(200)


def set_password(m, field_id, value=""):
    """Unmask a Moodle passwordunmask field right before typing (avoids blur re-hide)."""
    if not value:
        return
    edit_btn = "css=#fitem_%s [data-passwordunmask='edit']" % field_id
    if m.visible(edit_btn):
        m.click(edit_btn)
    m.type("id=" + field_id, value)


def verify_visible(m, locator):
    """Assert that a DOM element is currently displayed to the user."""
    assert m.visible(locator), "Element should be visible: %s" % locator


def verify_hidden(m, locator):
    """Assert that a DOM element is currently hidden from the user."""
    assert not m.visible(locator), "Element should be hidden: %s" % locator
