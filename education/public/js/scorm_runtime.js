class Scorm2004API {
    constructor(options = {}) {
        this.options = {
            autocommit: true,
            commitInterval: 10000,
            ...options
        };
        
        this.cmi = {
            "cmi.score.raw": "",
            "cmi.score.max": "",
            "cmi.score.min": "",
            "cmi.completion_status": "not attempted",
            "cmi.success_status": "unknown",
            "cmi.session_time": "0000:00:00",
            "cmi.interactions": []
        };
        
        this.events = {};
        this.lastCommit = Date.now();
        
        if (this.options.autocommit) {
            this.startAutoCommit();
        }
    }
    
    on(event, callback) {
        if (!this.events[event]) {
            this.events[event] = [];
        }
        this.events[event].push(callback);
    }
    
    emit(event, data) {
        if (this.events[event]) {
            this.events[event].forEach(callback => callback(data));
        }
    }
    
    startAutoCommit() {
        setInterval(() => {
            if (Date.now() - this.lastCommit > this.options.commitInterval) {
                this.commit();
            }
        }, this.options.commitInterval);
    }
    
    commit() {
        this.emit("Commit", this.cmi);
        this.lastCommit = Date.now();
    }
    
    terminate() {
        this.emit("Terminate", this.cmi);
    }
    
    // SCORM 2004 API Implementation
    LMSInitialize(param) {
        return "true";
    }
    
    LMSFinish(param) {
        this.terminate();
        return "true";
    }
    
    LMSGetValue(element) {
        if (element.startsWith("cmi.")) {
            const value = this.cmi[element];
            return value !== undefined ? value : "";
        }
        return "";
    }
    
    LMSSetValue(element, value) {
        if (element.startsWith("cmi.")) {
            this.cmi[element] = value;
            
            if (this.options.autocommit) {
                this.commit();
            }
            
            return "true";
        }
        return "false";
    }
    
    LMSCommit(param) {
        this.commit();
        return "true";
    }
    
    LMSGetLastError() {
        return "0";
    }
    
    LMSGetErrorString(errorCode) {
        return "";
    }
    
    LMSGetDiagnostic(errorCode) {
        return "";
    }
}

// Export for use in browser
window.Scorm2004API = Scorm2004API; 