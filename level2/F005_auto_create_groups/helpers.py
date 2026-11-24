"""Feature-specific helper for the F005 Level 2 flows (called with the 'helper' keyword).

Changing the enrolment status needs the edit link of one participant row, whose address contains a
database id; the helper reads that link from the page instead of hard-coding it.
"""


def set_enrolment_status(m, username, status):
    """Set the enrolment of `username` in KTC01 to 'Active' or 'Suspended'."""
    cid = m.course_id("KTC01")
    m.open("/user/index.php?id=%d&perpage=5000" % cid)
    link = "xpath=//tr[contains(.,'%s@example.com')]//a[@data-action='editenrolment']" % username
    m.open(m.attribute(link, "href"))
    m.select("id=id_status", status)
    m.submit("id=id_submitbutton")
