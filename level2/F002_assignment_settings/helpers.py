"""Feature-specific helpers for the F002 Level 2 flows.

Everything here is called from flows.csv with the `helper` keyword; the engine passes the
Moodle page helper and the remaining arguments (separated by ';' in the flow value).
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from common import config


def open_new_assignment(m):
    cid = m.course_id(config.COURSE_SHORTNAME)
    m.open("/course/modedit.php?add=assign&type=&course=%d&section=0&return=0" % cid)
    m.expand_all()
    m.wait("id=id_name", visible=True)


def delete_assignments(m):
    m.delete_activities("assign")


def set_reopen(m, value):
    if value:
        m.select("id=id_attemptreopenmethod", "value=" + value)


def ensure_time_limit(m):
    m.open("/admin/settings.php?section=modsettingassign")
    cb = "id=id_s_assign_enabletimelimit"
    if m.exists(cb) and not m.find(cb).is_selected():
        m.set_checkbox(cb, True)
        m.submit("xpath=//button[normalize-space(.)='Save changes']")


def ensure_grouping(m):
    cid = m.course_id(config.COURSE_SHORTNAME)
    m.open("/group/index.php?id=%d" % cid)
    names = [o.text.strip() for o in Select(m.find("id=groups")).options]
    if "G1" not in names:
        m.click("xpath=//button[normalize-space(.)='Create group']")
        m.wait("id=id_name", visible=True)
        m.type("id=id_name", "G1")
        m.submit("id=id_submitbutton")

    m.open("/group/groupings.php?id=%d" % cid)
    if "G1" not in m.text("id=region-main"):
        m.click("xpath=//button[normalize-space(.)='Create grouping']")
        m.wait("id=id_name", visible=True)
        m.type("id=id_name", "G1")
        m.submit("id=id_submitbutton")

    m.open("/group/groupings.php?id=%d" % cid)
    rows = m.d.find_elements(By.XPATH, "//tr[td[normalize-space(.)='G1']]")
    if rows and "None" in rows[0].text:
        links = rows[0].find_elements(By.XPATH, ".//a[contains(@href,'/group/assign.php?id=')]")
        if links:
            m.open(links[0].get_attribute("href"))
            options = m.d.find_elements(By.CSS_SELECTOR, "select#addselect option")
            if options:
                m.d.execute_script("arguments[0].selected=true;", options[0])
                m.submit("id=add")


def remove_grouping(m):
    """Best-effort cleanup of the temporary G1 grouping and group."""
    try:
        cid = m.course_id(config.COURSE_SHORTNAME)
        m.open("/group/groupings.php?id=%d" % cid)
        for link in m.d.find_elements(
                By.XPATH,
                "//tr[td[normalize-space(.)='G1']]//a[contains(@href,'grouping.php') and contains(@href,'delete=1')]"):
            m.open(link.get_attribute("href"))
            if m.exists("xpath=//button[contains(@class,'btn-danger')]"):
                m.click("xpath=//button[contains(@class,'btn-danger')]")
        m.open("/group/index.php?id=%d" % cid)
        for link in m.d.find_elements(
                By.XPATH,
                "//tr[td[normalize-space(.)='G1']]//a[contains(@href,'group.php') and contains(@href,'delete=1')]"):
            m.open(link.get_attribute("href"))
            if m.exists("xpath=//button[contains(@class,'btn-danger')]"):
                m.click("xpath=//button[contains(@class,'btn-danger')]")
    except Exception as e:
        print("  note: grouping cleanup skipped: %s" % str(e).splitlines()[0])


def open_assignment_settings(m, name):
    m.open("/course/view.php?name=" + config.COURSE_SHORTNAME)
    if "'" not in name:
        loc = "xpath=//a[contains(@href,'/mod/assign/view.php?id=') and contains(normalize-space(.),'%s')]" % name
    else:
        loc = "xpath=//a[contains(@href,'/mod/assign/view.php?id=') and contains(normalize-space(.),%s)]" % (
            "concat('%s')" % "', \"'\", '".join(name.split("'")))
    m.click(loc)
    link = "xpath=//a[contains(@href,'modedit.php?update=')]"
    m.open(m.attribute(link, "href"))
    m.expand_all()
