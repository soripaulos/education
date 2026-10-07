"""Student lifecycle: enrollment, sections, exits, accounts and diagnostics.

The pieces of a school year that used to be handled one tool at a time live
here so they agree with each other:

* ``common``      - grade ordering, program/stream parsing, name matching.
* ``reconcile``   - lines last year's students up against this year's
                    applications and decides what each one needs.
* ``roster``      - reads the class lists (School ID -> Section) staff upload.
* ``groups``      - section membership by year, and the yearly group rollover.
* ``exits``       - what leaving (and coming back) does to a Student.
* ``accounts``    - student logins, created separately from enrollment.
* ``diagnostics`` - everything that is out of step, as one list.
"""
