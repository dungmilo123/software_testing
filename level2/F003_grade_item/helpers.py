"""Feature-specific helpers for the F003 Level 2 flows (called with the 'helper' keyword: fn(moodle, *args)).

They cover what the keyword engine cannot express on its own:
  * a loop (delete every grade item / category left by a case),
  * an address that contains a database id read from the page (Single view of one grade item),
  * the course reset of the gradebook and the regrade task it queues (the demo container has no cron).
"""
COURSE = "KTC01"
ROW = "xpath=//tr[@data-itemid][.//span[contains(@class,'gradeitemheader') and normalize-space(.)='%s']]"
CONFIRM = "xpath=//div[contains(@class,'modal') and contains(@class,'show')]//button[%s]"


def _setup_page(m):
    m.open("/grade/edit/tree/index.php?id=%d" % m.course_id(COURSE))
    m.dismiss_tour()
    m.pause(1000)


def delete_all_items(m):
    """Delete every manual grade item, then every grade category, through the row menus (Delete)."""
    rows = ("//tr[@data-itemid][contains(@class,'item')][not(contains(@class,'courseitem'))]"
            "[not(contains(@class,'categoryitem'))]",
            "//tr[@data-category][contains(@class,'category')][not(contains(@class,'coursecategory'))]")
    for _ in range(40):
        _setup_page(m)
        if m.exists("xpath=//p[contains(@class,'errormessage')]"):  # broken gradebook: only a reset helps
            reset_gradebook(m)
            return
        target = next((r for r in rows if m.exists("xpath=" + r)), None)
        if target is None:
            return
        first = "xpath=(%s)[1]" % target
        m.click(first + "//button[contains(@class,'cellmenubtn')]")
        m.click(first + "//a[@aria-label='Delete']")
        m.submit(CONFIRM % "normalize-space(.)='Delete'")


def reset_gradebook(m):
    """Course reset with only 'Delete all items and categories', then run the queued regrade task."""
    cid = m.course_id(COURSE)
    m.open("/course/reset.php?id=%d" % cid)
    m.click("id=id_deselectall")
    m.expand_all()
    m.set_checkbox("id=id_reset_gradebook_items", True)
    m.click("id=id_submitbutton")
    m.submit(CONFIRM % "@data-action='delete'")
    m.wait("xpath=//table//tr[td[normalize-space(.)='All items and categories'] and td[normalize-space(.)='Done']]")
    m.open("/grade/report/grader/index.php?id=%d" % cid)
    m.dismiss_tour()
    if m.exists("xpath=//a[normalize-space(.)='Run now']"):
        m.submit("xpath=//a[normalize-space(.)='Run now']")
        if m.exists("xpath=//button[normalize-space(.)='Run ad hoc tasks now?']"):
            m.submit("xpath=//button[normalize-space(.)='Run ad hoc tasks now?']")
        m.wait("xpath=//*[contains(text(),'Regrade complete.')]", timeout=60)


def open_singleview(m, item):
    """Open Single view of one grade item (its id is read from the Gradebook setup row)."""
    _setup_page(m)
    itemid = m.attribute(ROW % item, "data-itemid")
    m.open("/grade/report/singleview/index.php?id=%d&item=grade&itemid=%s" % (m.course_id(COURSE), itemid))
    m.pause(1500)


def set_grade(m, item, student, grade):
    """Enter one grade in Single view (turns Edit mode on first if it is off)."""
    open_singleview(m, item)
    if not m.find("css=input[name='setmode']").is_selected():
        m.click("css=input[name='setmode']")
        m.wait_ready()
        m.pause(1500)
    m.type("xpath=//tr[.//a[contains(normalize-space(.),'%s')]]//input[starts-with(@name,'finalgrade_')]" % student,
           grade)
    m.submit("xpath=//input[@type='submit' and @value='Save']")
    m.wait("xpath=//div[contains(@class,'alert') and contains(.,'Grades were set for 1 items')]")
