# Student Lifecycle: enrolling a new year, leavers, logins and exams

Everything below is on the **Student Lifecycle** workspace.

## The yearly sequence

1. **Applications come in** through the registration pages. A student's
   application for the new year is the source of truth: it says whether
   they are coming back and which grade they are going into. A student who
   was not promoted applies for the same grade again (the registration page
   pins the grade for anyone on the *Not Promoted Student* list).

2. **Check Enrollment Diagnostics** (report). It lists every gap, graded:
   - **Blocked** - must be fixed first (usually on the application), e.g. a
     student on the Not Promoted list who applied for the next grade, or a
     School ID that belongs to somebody else.
   - **Review** - needs a decision, e.g. repeating without being on the Not
     Promoted list, skipping a grade, a disabled or restricted student, a
     section of another grade/branch/medium.
   - **Info** - worth knowing, e.g. Dembi Dollo students who will get a
     Student record, leavers, students with no login yet.

3. **Program Enrollment Tool**
   - Choose *From* (last) and *To* (new) academic year. Optionally filter by
     program or branch.
   - Upload the **section roster** (.xlsx/.csv). Either one sheet with
     *School ID* and *Section* columns, or one sheet per section named after
     it. Students on the roster go into that section; others fall back to
     the section suggested at registration (only if it is the right grade
     and branch).
   - **Load Students.** Ready rows are set to *Enroll*; Review rows are set
     to *Skip* until you check them; Blocked rows can never be enrolled.
     Students with no application appear as *Not Returning*; Grade 12
     students as *Graduating* (set to *Record Exit*).
   - **Process Rows.** Runs in the background. It creates Student records
     for new students (without logins), submits the enrollments with their
     section, readmits anyone who had left, and records exits for rows set
     to *Record Exit*. Each row is re-checked on the server first.

4. **Roll Over Student Groups** (same tool, once enrollment is done). Each
   section used in the new year is moved onto it and filled with the
   students enrolled into it (alphabetical roll numbers). Before anything is
   replaced, every student's previous section is saved on their previous
   enrollment, so last year's results, rankings and reports keep working.
   Missing sections from the roster are created; homeroom teachers are kept.

5. **Student User Creation Tool.** Filter (year / program / section /
   branch), load, and create logins in one go - no hourly limit. Login: the
   school address for the School ID. Initial password: the family phone
   number written locally (`0912345678`), or `251912345678` if the password
   policy rejects that. A private CSV of logins and initial passwords is
   attached for handing out. No emails are sent.

6. **Leavers.** Once registration has closed, set *Not Returning* rows to
   *Record Exit* (bulk button), or record individual exits from the Student
   form (**Record Exit**).

## Student Exit

One record per departure: Graduated, Transferred, Withdrawn, Did Not
Re-register, Expelled, Deceased, Other. On submit the Student is disabled
with its leaving date, reason and certificate number; it is removed from
active sections and its login is disabled. Cancelling the exit restores all
of that.

After submission you can still complete the clearance, the leaving
certificate, the after-school destination and the **Documents Issued**
table, so transcripts handed out years later are recorded on the same
document. A student who comes back is *readmitted* by the enrollment tool;
the exit stays on file marked Readmitted.

## External Exam Result

Grade 6 and Grade 8 regional exams and the Grade 12 national exam: one
record per student per exam and year, a row per subject, with total,
average and Pass/Fail against the pass mark (defaults in *Education
Settings*). A Grade 12 result is linked to the student's graduation exit
automatically. A failed regional exam flags the student for review if they
applied for the next grade. See the **External Exam Analysis** report for
pass rates and subject averages.

## Settings (Education Settings > Promotion & Exams)

- *Promotion Pass Mark* - year average below which a promoted student is
  noted in the enrollment tool (and report cards suggest "Detained").
- *Regional / National Exam Pass Mark* - default pass marks for exam results.

## Deploying

`bench --site <site> migrate` creates the new doctypes and fields and runs
`student_lifecycle_setup`, which gives every section its branch and records
each student's current section on their enrollment for that year.
