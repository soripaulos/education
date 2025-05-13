export class ScormAPI {
  constructor({ packageId, onCommit }) {
    this.packageId = packageId
    this.onCommit = onCommit
    this.cmi = {
      core: {
        student_id: '',
        student_name: '',
        lesson_location: '',
        credit: 'credit',
        lesson_status: 'not attempted',
        score: {
          raw: '',
          min: '',
          max: ''
        },
        session_time: '0000:00:00',
        total_time: '0000:00:00'
      },
      interactions: [],
      objectives: []
    }

    // Initialize both API_1484_11 and API for better compatibility
    window.API_1484_11 = this
    window.API = this
  }

  // SCORM 2004 API Methods
  Initialize(param) {
    console.log('SCORM Initialize called with:', param)
    return 'true'
  }

  Terminate(param) {
    console.log('SCORM Terminate called with:', param)
    this.onCommit(this.cmi)
    return 'true'
  }

  GetValue(element) {
    console.log('SCORM GetValue called for:', element)
    const value = this.getCMIValue(element)
    return value !== undefined ? value : ''
  }

  SetValue(element, value) {
    console.log('SCORM SetValue called for:', element, 'with value:', value)
    this.setCMIValue(element, value)
    return 'true'
  }

  Commit(param) {
    console.log('SCORM Commit called with:', param)
    this.onCommit(this.cmi)
    return 'true'
  }

  GetLastError() {
    return '0'
  }

  GetErrorString(errorCode) {
    return 'No error'
  }

  GetDiagnostic(errorCode) {
    return 'No error'
  }

  // Helper methods
  getCMIValue(element) {
    const parts = element.split('.')
    let current = this.cmi

    for (const part of parts) {
      if (current[part] === undefined) {
        return undefined
      }
      current = current[part]
    }

    return current
  }

  setCMIValue(element, value) {
    const parts = element.split('.')
    let current = this.cmi

    for (let i = 0; i < parts.length - 1; i++) {
      const part = parts[i]
      if (current[part] === undefined) {
        current[part] = {}
      }
      current = current[part]
    }

    const lastPart = parts[parts.length - 1]
    current[lastPart] = value

    // Auto-commit on important changes
    if (element.includes('completion_status') || 
        element.includes('success_status') || 
        element.includes('score.raw')) {
      this.onCommit(this.cmi)
    }
  }

  terminate() {
    if (this.onCommit) {
      this.onCommit(this.cmi)
    }
    delete window.API_1484_11
    delete window.API
  }
} 