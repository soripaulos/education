(function () {
  const root = document.getElementById("roster-page-root");
  if (!root) {
    return;
  }

  const configNode = document.getElementById("roster-config");
  const safeParse = (value, fallback) => {
    if (!value) return fallback;
    try {
      return JSON.parse(value);
    } catch (err) {
      console.warn("[Roster] Failed to parse config JSON", err);
      return fallback;
    }
  };

  const config = {
    defaultYear: configNode?.dataset.defaultYear || "",
    semesters: safeParse(configNode?.dataset.semesters, []),
    exams: safeParse(configNode?.dataset.exams, []),
    examMaxMap: safeParse(configNode?.dataset.examMap, {}),
  };

  const escapeHtml = (value) => {
    const str = value === undefined || value === null ? "" : String(value);
    if (frappe.utils && frappe.utils.escape_html) {
      return frappe.utils.escape_html(str);
    }
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  };

  class RosterPage {
    constructor(rootEl, config) {
      this.root = rootEl;
      this.config = config;
      this.state = {
        studentGroup: "",
        program: "",
        students: [],
        subjects: [],
        selectedSubject: "",
        selectedExam: "",
        academicYear: config.defaultYear,
        semester: config.semesters?.[0] || "",
        scoreRows: {},
        inputValues: {},
        existingScoresByExam: {},
        queue: [],
        loading: false,
      };
    }

    init() {
      this.cacheElements();
      this.bindEvents();
      this.loadStudentGroups();
      this.updateActionStates();
      this.updateStatus(__("Select a Student Group to begin."));
    }

    cacheElements() {
      this.elements = {
        studentGroupSelect: document.getElementById("roster-student-group"),
        programInput: document.getElementById("roster-program"),
        academicYearInput: document.getElementById("roster-academic-year"),
        semesterSelect: document.getElementById("roster-semester"),
        subjectSelect: document.getElementById("roster-subject"),
        examSelect: document.getElementById("roster-exam"),
        maxScoreInput: document.getElementById("roster-max-score"),
        refreshButton: document.getElementById("roster-refresh-scores"),
        queueButton: document.getElementById("roster-queue-btn"),
        submitButton: document.getElementById("roster-submit-btn"),
        clearQueueButton: document.getElementById("roster-clear-queue-btn"),
        deleteExistingButton: document.getElementById("roster-delete-existing-btn"),
        statusText: document.getElementById("roster-status-text"),
        scoreCount: document.getElementById("roster-score-count"),
        scoreTableBody: document.getElementById("roster-score-table-body"),
        summaryBody: document.getElementById("roster-summary-body"),
        queueBody: document.getElementById("roster-queue-body"),
        queueCount: document.getElementById("roster-queue-count"),
      };
    }

    bindEvents() {
      this.elements.studentGroupSelect.addEventListener("change", () => this.handleGroupChange());
      this.elements.subjectSelect.addEventListener("change", () => this.handleSubjectChange());
      this.elements.examSelect.addEventListener("change", () => this.handleExamChange());
      this.elements.academicYearInput.addEventListener("change", () => this.handleYearChange());
      this.elements.semesterSelect.addEventListener("change", () => this.handleSemesterChange());
      this.elements.refreshButton.addEventListener("click", (event) => {
        event.preventDefault();
        this.refreshCurrentExamScores();
      });
      this.elements.queueButton.addEventListener("click", (event) => {
        event.preventDefault();
        this.handleQueueScores();
      });
      this.elements.submitButton.addEventListener("click", (event) => {
        event.preventDefault();
        this.handleSubmitQueue();
      });
      this.elements.clearQueueButton.addEventListener("click", (event) => {
        event.preventDefault();
        this.clearQueue();
      });
      this.elements.deleteExistingButton.addEventListener("click", (event) => {
        event.preventDefault();
        this.handleDeleteExisting();
      });
    }

    setLoading(isLoading) {
      this.state.loading = isLoading;
      const controls = [
        this.elements.studentGroupSelect,
        this.elements.subjectSelect,
        this.elements.examSelect,
        this.elements.academicYearInput,
        this.elements.semesterSelect,
        this.elements.refreshButton,
        this.elements.queueButton,
        this.elements.submitButton,
        this.elements.clearQueueButton,
        this.elements.deleteExistingButton,
      ];
      controls.forEach((el) => {
        if (!el) return;
        if (isLoading) {
          el.dataset.prevDisabled = el.disabled ? "1" : "0";
          el.disabled = true;
        } else if (el.dataset.prevDisabled) {
          el.disabled = el.dataset.prevDisabled === "1";
          delete el.dataset.prevDisabled;
        }
      });
      this.updateActionStates();
    }

    updateStatus(message, tone = "muted") {
      if (this.elements.statusText) {
        this.elements.statusText.textContent = message;
        this.elements.statusText.className = `text-${tone} mt-2 mb-0`;
      }
    }

    async loadStudentGroups() {
      this.setLoading(true);
      this.updateStatus(__("Loading student groups..."), "info");
      try {
        const response = await frappe.call({
          method: "education.api.roster.get_student_groups",
        });
        const groups = response.message || [];
        this.populateStudentGroupOptions(groups);
        this.updateStatus(
          groups.length
            ? __("Student groups loaded. Select one to continue.")
            : __("No student groups available."),
          groups.length ? "success" : "danger"
        );
      } catch (error) {
        console.error(error);
        frappe.msgprint({
          title: __("Roster"),
          message: __("Unable to load student groups. Please try again."),
          indicator: "red",
        });
        this.updateStatus(__("Failed to load student groups."), "danger");
      } finally {
        this.setLoading(false);
      }
    }

    populateStudentGroupOptions(groups) {
      const select = this.elements.studentGroupSelect;
      select.innerHTML = `<option value="">${__("Select a Student Group")}</option>`;
      groups.forEach((group) => {
        const option = document.createElement("option");
        option.value = group.name;
        option.textContent = `${group.student_group_name || group.name}`;
        option.dataset.program = group.program || "";
        select.appendChild(option);
      });
      select.removeAttribute("disabled");
    }

    async handleGroupChange() {
      const value = this.elements.studentGroupSelect.value;
      this.resetStateForNewGroup();
      if (!value) {
        this.updateStatus(__("Select a Student Group to begin."), "muted");
        return;
      }

      this.state.studentGroup = value;
      this.setLoading(true);
      this.updateStatus(__("Loading student group details..."), "info");

      try {
        const response = await frappe.call({
          method: "education.api.roster.get_student_group_students",
          args: { student_group: value },
        });

        const { group, students } = response.message || {};
        this.state.students = students || [];
        this.state.program = group?.program || "";
        this.elements.programInput.value = this.state.program || "";
        this.elements.programInput.readOnly = true;

        const academicYear = group?.academic_year || this.config.defaultYear;
        this.elements.academicYearInput.value = academicYear;
        this.state.academicYear = academicYear;

        this.renderStudents();
        this.updateStatus(__("Student group loaded. Select a subject to continue."), "success");

        if (this.state.program) {
          await this.loadProgramSubjects(this.state.program);
        } else {
          this.updateStatus(__("No program found on this student group."), "warning");
        }
      } catch (error) {
        console.error(error);
        frappe.msgprint({
          title: __("Roster"),
          message: __("Unable to load the selected student group."),
          indicator: "red",
        });
        this.updateStatus(__("Failed to load student group."), "danger");
      } finally {
        this.setLoading(false);
      }
    }

    resetStateForNewGroup() {
      this.state.studentGroup = "";
      this.state.program = "";
      this.state.students = [];
      this.state.subjects = [];
      this.state.selectedSubject = "";
      this.state.selectedExam = "";
      this.state.scoreRows = {};
      this.state.inputValues = {};
      this.state.existingScoresByExam = {};
      this.clearQueue();
      this.elements.subjectSelect.value = "";
      this.elements.subjectSelect.setAttribute("disabled", "disabled");
      this.elements.examSelect.value = "";
      this.elements.examSelect.setAttribute("disabled", "disabled");
      this.elements.maxScoreInput.value = "";
      this.elements.refreshButton.setAttribute("disabled", "disabled");
      this.elements.deleteExistingButton.setAttribute("disabled", "disabled");
      this.elements.programInput.value = "";
      this.renderStudents();
      this.renderSubjectOptions([]);
      this.updateSummaryTable();
    }

    async loadProgramSubjects(program) {
      this.updateStatus(__("Loading subjects for program {0}").format(program), "info");
      try {
        const response = await frappe.call({
          method: "education.api.roster.get_program_subjects",
          args: { program },
        });
        const subjects = response.message || [];
        this.state.subjects = subjects;
        this.renderSubjectOptions(subjects);
        if (subjects.length === 0) {
          this.updateStatus(
            __("No subjects are linked with this program. Please update the Program document."),
            "warning"
          );
        } else {
          this.updateStatus(__("Select a subject to load scores."), "success");
        }
      } catch (error) {
        console.error(error);
        frappe.msgprint({
          title: __("Roster"),
          message: __("Unable to load program subjects."),
          indicator: "red",
        });
        this.updateStatus(__("Failed to load program subjects."), "danger");
      }
    }

    renderSubjectOptions(subjects) {
      const select = this.elements.subjectSelect;
      select.innerHTML = `<option value="">${__("Select a subject")}</option>`;
      subjects.forEach((subject) => {
        const option = document.createElement("option");
        option.value = subject.name;
        option.textContent = subject.course_name || subject.name;
        select.appendChild(option);
      });
      if (subjects.length) {
        select.removeAttribute("disabled");
        this.elements.examSelect.removeAttribute("disabled");
      } else {
        select.setAttribute("disabled", "disabled");
        this.elements.examSelect.setAttribute("disabled", "disabled");
      }
    }

    handleSubjectChange() {
      this.state.selectedSubject = this.elements.subjectSelect.value;
      this.state.existingScoresByExam = {};
      this.state.inputValues = {};
      this.clearQueue();
      this.renderStudents();
      this.updateSummaryTable();
      this.updateActionStates();
      if (this.state.selectedSubject && this.state.selectedExam) {
        this.refreshCurrentExamScores();
      } else if (this.state.selectedSubject) {
        this.loadSummaryForAllExams();
      }
    }

    handleExamChange() {
      this.state.selectedExam = this.elements.examSelect.value;
      const maxScore = this.config.examMaxMap[this.state.selectedExam] || "";
      this.elements.maxScoreInput.value = maxScore ? `${maxScore}` : "";
      this.state.inputValues = {};
      this.clearQueue();
      this.renderStudents();
      this.updateSummaryTable();
      this.updateActionStates();
      if (this.state.selectedSubject && this.state.selectedExam) {
        this.refreshCurrentExamScores();
      }
    }

    handleYearChange() {
      this.state.academicYear = this.elements.academicYearInput.value || this.config.defaultYear;
      if (this.canRefresh()) {
        this.refreshCurrentExamScores();
      }
    }

    handleSemesterChange() {
      this.state.semester = this.elements.semesterSelect.value || this.config.semesters?.[0] || "";
      if (this.canRefresh()) {
        this.refreshCurrentExamScores();
      }
    }

    renderStudents() {
      const tbody = this.elements.scoreTableBody;
      tbody.innerHTML = "";

      if (!this.state.students.length) {
        tbody.innerHTML = `
          <tr class="roster-empty-row">
            <td colspan="6" class="text-center text-muted p-4">
              ${__("Student data will appear here once a group is selected.")}
            </td>
          </tr>
        `;
        this.elements.scoreCount.textContent = __("0 students loaded");
        return;
      }

      this.state.scoreRows = {};
      const fragment = document.createDocumentFragment();
      this.state.students.forEach((student, index) => {
        const row = document.createElement("tr");
        row.dataset.student = student.student;
        const inputId = `score-input-${index}`;
        row.innerHTML = `
          <td>${escapeHtml(student.group_roll_number || "")}</td>
          <td>${escapeHtml(student.student)}</td>
          <td>${escapeHtml(student.student_name || "")}</td>
          <td><span class="status-pill none">${__("None")}</span></td>
          <td>
            <input type="number" min="0" step="0.01" class="form-control form-control-sm score-input"
              id="${inputId}" data-student="${student.student}" autocomplete="off" ${this.state.selectedExam ? "" : "disabled"}>
          </td>
          <td class="max-score-cell">${this.elements.maxScoreInput.value || "--"}</td>
        `;
        fragment.appendChild(row);
        const input = row.querySelector("input");
        this.state.scoreRows[student.student] = {
          row,
          input,
          statusPill: row.querySelector(".status-pill"),
          maxCell: row.querySelector(".max-score-cell"),
        };
        this.attachInputHandlers(input, student.student);
      });

      tbody.appendChild(fragment);
      this.updateScoreCount();
      this.updateSummaryTable();
    }

    updateScoreCount() {
      this.elements.scoreCount.textContent = __("{0} students loaded").format(this.state.students.length);
    }

    attachInputHandlers(input, studentId) {
      input?.addEventListener("input", () => this.handleScoreInputChange(studentId));
      input?.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
          event.preventDefault();
          this.focusNextInput(studentId);
        }
      });
    }

    handleScoreInputChange(studentId) {
      const rowInfo = this.state.scoreRows[studentId];
      if (!rowInfo || !rowInfo.input) {
        return;
      }
      const value = rowInfo.input.value;
      const maxScore = this.config.examMaxMap[this.state.selectedExam];

      let isValid = true;
      if (value === "") {
        isValid = false;
      } else {
        const numericValue = parseFloat(value);
        if (isNaN(numericValue) || numericValue < 0 || (maxScore && numericValue > maxScore)) {
          isValid = false;
        }
      }

      if (!isValid) {
        rowInfo.input.classList.add("invalid");
      } else {
        rowInfo.input.classList.remove("invalid");
      }

      const existingScore =
        this.state.existingScoresByExam[this.state.selectedExam]?.[studentId]?.score ?? null;
      const numericValue = value === "" ? null : parseFloat(value);
      const isDirty = isValid && numericValue !== null && numericValue !== existingScore;

      if (isDirty) {
        rowInfo.input.classList.add("dirty");
      } else {
        rowInfo.input.classList.remove("dirty");
      }

      this.state.inputValues[studentId] = {
        value: numericValue,
        valid: isValid,
        dirty: isDirty,
      };

      this.updateActionStates();
      this.updateSummaryTable();
    }

    focusNextInput(studentId) {
      const ids = this.state.students.map((student) => student.student);
      const idx = ids.indexOf(studentId);
      if (idx === -1) return;
      const nextId = ids[idx + 1];
      if (!nextId) return;
      const nextInput = this.state.scoreRows[nextId]?.input;
      nextInput?.focus();
    }

    canRefresh() {
      return Boolean(
        this.state.studentGroup &&
          this.state.selectedSubject &&
          this.state.selectedExam &&
          this.state.academicYear &&
          this.state.semester
      );
    }

    updateActionStates() {
      const hasDirty = Object.values(this.state.inputValues).some((value) => value.dirty && value.valid);
      const hasQueue = this.state.queue.length > 0;

      if (this.canRefresh() && !this.state.loading) {
        this.elements.refreshButton.removeAttribute("disabled");
      } else {
        this.elements.refreshButton.setAttribute("disabled", "disabled");
      }

      if (hasDirty && !this.state.loading) {
        this.elements.queueButton.removeAttribute("disabled");
      } else {
        this.elements.queueButton.setAttribute("disabled", "disabled");
      }

      if (hasQueue && !this.state.loading) {
        this.elements.submitButton.removeAttribute("disabled");
        this.elements.clearQueueButton.removeAttribute("disabled");
      } else {
        this.elements.submitButton.setAttribute("disabled", "disabled");
        this.elements.clearQueueButton.setAttribute("disabled", "disabled");
      }

      const existingEntries = Object.keys(
        this.state.existingScoresByExam[this.state.selectedExam] || {}
      ).length;
      if (existingEntries && !this.state.loading) {
        this.elements.deleteExistingButton.removeAttribute("disabled");
      } else {
        this.elements.deleteExistingButton.setAttribute("disabled", "disabled");
      }
    }

    collectDirtyEntries() {
      const entries = [];
      Object.entries(this.state.inputValues).forEach(([studentId, info]) => {
        if (!info.dirty || !info.valid) {
          return;
        }
        const student = this.state.students.find((row) => row.student === studentId);
        if (!student) {
          return;
        }
        const existing = this.state.existingScoresByExam[this.state.selectedExam]?.[studentId];
        entries.push({
          student: student.student,
          student_name: student.student_name,
          student_group: this.state.studentGroup,
          subject: this.state.selectedSubject,
          exam: this.state.selectedExam,
          academic_year: this.state.academicYear,
          semester: this.state.semester,
          grade: this.state.program,
          score: info.value,
          max_score: this.config.examMaxMap[this.state.selectedExam],
          name: existing?.name,
        });
      });
      return entries;
    }

    handleQueueScores() {
      const entries = this.collectDirtyEntries();
      if (!entries.length) {
        frappe.show_alert({ message: __("No valid score changes to queue."), indicator: "orange" });
        return;
      }
      entries.forEach((entry) => this.upsertQueueEntry(entry));
      frappe.show_alert({
        message: __("{0} score(s) added to the queue.").format(entries.length),
        indicator: "green",
      });
      this.resetDirtyInputs();
      this.refreshQueueTable();
      this.updateActionStates();
      this.updateSummaryTable();
    }

    upsertQueueEntry(entry) {
      const key = `${entry.student}-${entry.subject}-${entry.exam}`;
      const existingIndex = this.state.queue.findIndex(
        (item) => `${item.student}-${item.subject}-${item.exam}` === key
      );
      if (existingIndex > -1) {
        this.state.queue.splice(existingIndex, 1, { ...entry, id: this.state.queue[existingIndex].id });
      } else {
        entry.id = `${Date.now()}-${key}`;
        this.state.queue.push(entry);
      }
    }

    resetDirtyInputs() {
      Object.values(this.state.scoreRows).forEach((rowInfo) => {
        if (!rowInfo?.input) return;
        rowInfo.input.classList.remove("dirty");
      });
      Object.keys(this.state.inputValues).forEach((studentId) => {
        this.state.inputValues[studentId].dirty = false;
      });
    }

    refreshQueueTable() {
      const tbody = this.elements.queueBody;
      tbody.innerHTML = "";

      if (!this.state.queue.length) {
        tbody.innerHTML = `
          <tr class="roster-empty-row">
            <td colspan="5" class="text-center text-muted p-4">
              ${__("No queued submissions yet. Queue validated scores before submitting.")}
            </td>
          </tr>
        `;
        this.elements.queueCount.textContent = "0";
        this.updateActionStates();
        return;
      }

      const fragment = document.createDocumentFragment();
      this.state.queue.forEach((entry) => {
        const row = document.createElement("tr");
        row.innerHTML = `
          <td>${escapeHtml(entry.student_name)} (${escapeHtml(entry.student)})</td>
          <td>${escapeHtml(entry.subject)}</td>
          <td>${escapeHtml(entry.exam)}</td>
          <td>${entry.score} / ${entry.max_score}</td>
          <td><button class="queue-remove-btn" data-entry="${entry.id}">${__("Remove")}</button></td>
        `;
        fragment.appendChild(row);
      });
      tbody.appendChild(fragment);
      this.elements.queueCount.textContent = String(this.state.queue.length);
      tbody.querySelectorAll(".queue-remove-btn").forEach((button) => {
        button.addEventListener("click", (event) => {
          const entryId = event.currentTarget.dataset.entry;
          this.removeQueueEntry(entryId);
        });
      });
      this.updateActionStates();
    }

    removeQueueEntry(entryId) {
      this.state.queue = this.state.queue.filter((entry) => entry.id !== entryId);
      this.refreshQueueTable();
      this.updateSummaryTable();
    }

    clearQueue() {
      this.state.queue = [];
      if (this.elements.queueBody) {
        this.refreshQueueTable();
      }
      this.updateActionStates();
    }

    async handleSubmitQueue() {
      if (!this.state.queue.length) {
        return;
      }

      this.setLoading(true);
      this.updateStatus(__("Submitting queued scores..."), "info");

      try {
        const response = await frappe.call({
          method: "education.api.roster.save_scores_batch",
          args: { entries: this.state.queue },
          freeze: true,
          freeze_message: __("Submitting scores..."),
        });

        const { saved = [], errors = [] } = response.message || {};
        if (saved.length) {
          frappe.show_alert({
            message: __("{0} scores submitted successfully.").format(saved.length),
            indicator: "green",
          });
        }
        if (errors.length) {
          frappe.msgprint({
            title: __("Some scores failed to submit"),
            indicator: "orange",
              message: errors
                .map((error) => `<p>${escapeHtml(error.entry.student_name || error.entry.student)}: ${escapeHtml(error.error)}</p>`)
                .join(""),
          });
        }
        this.clearQueue();
        await this.refreshCurrentExamScores();
      } catch (error) {
        console.error(error);
        frappe.msgprint({
          title: __("Roster"),
          message: __("Unable to submit scores. Please check the queue and try again."),
          indicator: "red",
        });
      } finally {
        this.setLoading(false);
      }
    }

    async handleDeleteExisting() {
      if (!this.canRefresh()) {
        return;
      }
      frappe.confirm(
        __("Delete all existing scores for the selected context? This cannot be undone."),
        async () => {
          this.setLoading(true);
          try {
            await frappe.call({
              method: "education.api.roster.delete_scores",
              args: {
                filters: {
                  academic_year: this.state.academicYear,
                  semester: this.state.semester,
                  subject: this.state.selectedSubject,
                  student_group: this.state.studentGroup,
                  exam: this.state.selectedExam,
                },
              },
            });
            frappe.show_alert({ message: __("Existing scores deleted."), indicator: "green" });
            await this.refreshCurrentExamScores();
          } catch (error) {
            console.error(error);
            frappe.msgprint({
              title: __("Roster"),
              message: __("Unable to delete existing scores."),
              indicator: "red",
            });
          } finally {
            this.setLoading(false);
          }
        }
      );
    }

    async refreshCurrentExamScores() {
      if (!this.canRefresh()) {
        return;
      }
      this.updateStatus(__("Loading scores..."), "info");
      const exam = this.state.selectedExam;
      try {
        const rows = await this.fetchScoresForExam(exam);
        this.applyExistingScores(exam, rows, { updateInputs: true });
        await this.loadSummaryForAllExams(exam);
        this.updateStatus(__("Scores loaded."), "success");
      } catch (error) {
        console.error(error);
        this.updateStatus(__("Unable to fetch scores."), "danger");
        frappe.msgprint({
          title: __("Roster"),
          message: __("Unable to fetch existing scores."),
          indicator: "red",
        });
      } finally {
        this.updateActionStates();
      }
    }

    fetchScoresForExam(exam) {
      if (!exam) return Promise.resolve([]);
      return frappe
        .call({
          method: "education.api.roster.get_existing_scores",
          args: {
            academic_year: this.state.academicYear,
            semester: this.state.semester,
            subject: this.state.selectedSubject,
            student_group: this.state.studentGroup,
            exam,
          },
        })
        .then((response) => response.message || []);
    }

    applyExistingScores(exam, rows, options = {}) {
      const map = {};
      rows.forEach((row) => {
        map[row.student] = row;
      });
      this.state.existingScoresByExam[exam] = map;

      if (options.updateInputs && this.state.scoreRows) {
        Object.entries(this.state.scoreRows).forEach(([studentId, rowInfo]) => {
          const data = map[studentId];
          if (!rowInfo?.input) {
            return;
          }
          rowInfo.input.value = data?.score ?? "";
          if (this.state.selectedExam) {
            rowInfo.input.removeAttribute("disabled");
          }
          rowInfo.maxCell.textContent = this.config.examMaxMap[this.state.selectedExam] || "--";
          rowInfo.input.classList.remove("dirty", "invalid");
          this.state.inputValues[studentId] = {
            value: data?.score ?? null,
            valid: Boolean(data),
            dirty: false,
          };
          const statusPill = rowInfo.statusPill;
          if (data?.name) {
            const status = data.docstatus === 1 ? "submitted" : "draft";
            statusPill.textContent = data.docstatus === 1 ? __("Submitted") : __("Draft");
            statusPill.className = `status-pill ${status}`;
          } else {
            statusPill.textContent = __("None");
            statusPill.className = "status-pill none";
          }
        });
      }

      this.updateSummaryTable();
      this.updateActionStates();
    }

    async loadSummaryForAllExams(skipExam) {
      if (!this.state.selectedSubject || !this.state.studentGroup) {
        return;
      }
      for (const exam of this.config.exams.map((item) => item.value)) {
        if (skipExam && exam === skipExam) {
          continue;
        }
        try {
          const rows = await this.fetchScoresForExam(exam);
          this.applyExistingScores(exam, rows, { updateInputs: exam === this.state.selectedExam });
        } catch (error) {
          console.warn("[Roster] Unable to load summary for exam", exam, error);
        }
      }
      this.updateSummaryTable();
    }

    computeSummaryForStudent(studentId) {
      const summary = {};
      const queueOverrides = {};
      this.state.queue.forEach((entry) => {
        if (entry.student === studentId) {
          queueOverrides[entry.exam] = entry.score;
        }
      });

      this.config.exams.forEach((exam) => {
        const examKey = exam.value;
        let score = this.state.existingScoresByExam[examKey]?.[studentId]?.score ?? null;

        if (queueOverrides[examKey] !== undefined) {
          score = queueOverrides[examKey];
        }

        const inputValue = this.state.inputValues[studentId];
        if (
          this.state.selectedExam === examKey &&
          inputValue &&
          inputValue.valid &&
          inputValue.value !== null
        ) {
          score = inputValue.value;
        }

        summary[examKey] = score;
      });

      return summary;
    }

    updateSummaryTable() {
      const tbody = this.elements.summaryBody;
      tbody.innerHTML = "";

      if (!this.state.students.length) {
        tbody.innerHTML = `
          <tr class="roster-empty-row">
            <td colspan="6" class="text-center text-muted p-4">
              ${__("Summary will update automatically.")}
            </td>
          </tr>
        `;
        return;
      }

      const fragment = document.createDocumentFragment();
      this.state.students.forEach((student) => {
        const summary = this.computeSummaryForStudent(student.student);
        let total = 0;
        const cells = this.config.exams
          .map((exam) => {
            const score = summary[exam.value];
            if (typeof score === "number") {
              total += score;
              return `<td>${score}</td>`;
            }
            return "<td>--</td>";
          })
          .join("");
        const row = document.createElement("tr");
        row.innerHTML = `
          <td>${escapeHtml(student.student_name || student.student)}</td>
          ${cells}
          <td>${total ? total.toFixed(2) : "--"}</td>
        `;
        fragment.appendChild(row);
      });

      tbody.appendChild(fragment);
    }
  }

  frappe.ready(() => {
    const rosterPage = new RosterPage(root, config);
    rosterPage.init();
  });
})();
