// Vue.js Application
const { createApp } = Vue;

createApp({
    data() {
        return {
            currentStep: 1,
            totalSteps: 5,
            loading: true,
            isSubmitting: false,
            guardianType: 'parent',
            studentType: 'new',
            branchSelection: 'M1',
            existingStudent: null,
            existingSchoolId: '',
            schoolIdError: '',
            showSuccessModal: false,
            submittedApplicationId: '',
            fatherData: {
                guardian_name: '',
                email_address: '',
                mobile_number: '',
                alternate_number: '',
                education: '',
                occupation: '',
                work_address: '',
                education_other: '',
                occupation_other: ''
            },
            motherData: {
                guardian_name: '',
                email_address: '',
                mobile_number: '',
                alternate_number: '',
                education: '',
                occupation: '',
                work_address: '',
                education_other: '',
                occupation_other: ''
            },
            guardianData: {
                guardian_name: '',
                email_address: '',
                mobile_number: '',
                alternate_number: '',
                education: '',
                occupation: '',
                work_address: '',
                education_other: '',
                occupation_other: ''
            },
            studentData: {
                first_name: '',
                middle_name: '',
                last_name: '',
                gender: '',
                date_of_birth: '',
                program: '',
                primary_mobile_number: '',
                student_email_id: '',
                nationality: 'Ethiopian',
                academic_year: '2018 E.C.',
                custom_school_id: '',
                address_line_1: '',
                kebele: '',
                sub_city: '',
                city: 'Adama',
                state: 'Oromia',
                pincode: '',
                country: 'Ethiopia',
                image: ''
            },
            programs: [
                {name: 'Nursery', program_name: 'Nursery'},
                {name: 'LKG', program_name: 'LKG'},
                {name: 'UKG', program_name: 'UKG'},
                {name: 'Nursery AO', program_name: 'Nursery AO'},
                {name: 'LKG AO', program_name: 'LKG AO'},
                {name: 'UKG AO', program_name: 'UKG AO'},
                {name: 'Grade 1', program_name: 'Grade 1'},
                {name: 'Grade 2', program_name: 'Grade 2'},
                {name: 'Grade 3', program_name: 'Grade 3'},
                {name: 'Grade 4', program_name: 'Grade 4'},
                {name: 'Grade 5', program_name: 'Grade 5'},
                {name: 'Grade 6', program_name: 'Grade 6'},
                {name: 'Grade 7', program_name: 'Grade 7'},
                {name: 'Grade 8', program_name: 'Grade 8'},
                {name: 'Grade 1 AO', program_name: 'Grade 1 AO'},
                {name: 'Grade 2 AO', program_name: 'Grade 2 AO'},
                {name: 'Grade 3 AO', program_name: 'Grade 3 AO'},
                {name: 'Grade 4 AO', program_name: 'Grade 4 AO'},
                {name: 'Grade 5 AO', program_name: 'Grade 5 AO'},
                {name: 'Grade 6 AO', program_name: 'Grade 6 AO'},
                {name: 'Grade 7 AO', program_name: 'Grade 7 AO'},
                {name: 'Grade 8 AO', program_name: 'Grade 8 AO'},
                {name: 'Grade 9', program_name: 'Grade 9'},
                {name: 'Grade 10', program_name: 'Grade 10'},
                {name: 'Grade 11 NS', program_name: 'Grade 11 NS'},
                {name: 'Grade 12 NS', program_name: 'Grade 12 NS'},
                {name: 'Grade 11 SS', program_name: 'Grade 11 SS'},
                {name: 'Grade 12 SS', program_name: 'Grade 12 SS'}
            ],
            academicYears: [
                {name: '2018 E.C.', year_start_date: '2024-09-01', year_end_date: '2025-08-31'},
                {name: '2017 E.C.', year_start_date: '2023-09-01', year_end_date: '2024-08-31'},
                {name: '2019 E.C.', year_start_date: '2025-09-01', year_end_date: '2026-08-31'}
            ],
            educationLevels: [
                'No Formal Education', 'Primary Education', 'Secondary Education', 
                'High School', 'Diploma', 'Bachelor\'s Degree', 'Master\'s Degree', 
                'PhD', 'Other'
            ],
            occupations: [
                'Teacher', 'Doctor', 'Engineer', 'Lawyer', 'Businessman', 'Farmer', 
                'Government Employee', 'Private Employee', 'Self Employed', 'Student', 
                'Housewife', 'Retired', 'Other'
            ],
            validationErrors: {},
            phoneErrors: {},
            availableMobileNumbers: [],
            kebeleSubCityData: {},
            subCities: [],
            availableKebeles: [],
            sessionParentImages: {
                father: null,
                mother: null,
                guardian: null
            },
            sessionApplications: [],
            
            // Loading states
            isCheckingSchoolId: false,
            isUploadingFile: false,
            
            // Notifications
            notifications: []
        }
    },
    
    computed: {
        selectedProgramName() {
            const program = this.programs.find(p => p.name === this.studentData.program);
            return program ? program.program_name : this.studentData.program;
        },
        
        guardianMobileNumbers() {
            const numbers = [];
            if (this.guardianType === 'parent') {
                if (this.fatherData.mobile_number) {
                    numbers.push({
                        number: `+251${this.fatherData.mobile_number}`,
                        label: `Father: ${this.fatherData.guardian_name || 'Father'}`
                    });
                }
                if (this.motherData.mobile_number) {
                    numbers.push({
                        number: `+251${this.motherData.mobile_number}`,
                        label: `Mother: ${this.motherData.guardian_name || 'Mother'}`
                    });
                }
            } else {
                if (this.guardianData.mobile_number) {
                    numbers.push({
                        number: `+251${this.guardianData.mobile_number}`,
                        label: `Guardian: ${this.guardianData.guardian_name || 'Guardian'}`
                    });
                }
            }
            return numbers;
        },
        
        canProceed() {
            switch (this.currentStep) {
                case 1: // Guardian Information
                    if (this.guardianType === 'parent') {
                        return (
                            this.fatherData.guardian_name && 
                            this.fatherData.mobile_number && 
                            this.motherData.guardian_name && 
                            this.motherData.mobile_number &&
                            !this.phoneErrors.father &&
                            !this.phoneErrors.mother &&
                            !this.phoneErrors.father_alt &&
                            !this.phoneErrors.mother_alt
                        );
                    } else {
                        return (
                            this.guardianData.guardian_name && 
                            this.guardianData.mobile_number &&
                            !this.phoneErrors.guardian &&
                            !this.phoneErrors.guardian_alt
                        );
                    }
                case 2: // Student Type Selection
                    if (this.studentType === 'new') {
                        return this.branchSelection;
                    } else if (this.studentType === 'existing') {
                        return this.existingStudent !== null;
                    }
                    return false;
                case 3: // Home Address
                    return (
                        this.studentData.address_line_1 && 
                        this.studentData.sub_city &&
                        this.studentData.kebele
                    );
                case 4: // Student Details
                    return (
                        this.studentData.first_name && 
                        this.studentData.last_name && 
                        this.studentData.date_of_birth && 
                        this.studentData.program &&
                        this.studentData.student_email_id &&
                        this.studentData.image
                    );
                case 5: // Preview
                    return true;
                default:
                    return false;
            }
        },
        
        submitButtonText() {
            if (this.isSubmitting) {
                return 'Submitting...';
            }
            return 'Submit Application';
        }
    },
    
    async mounted() {
        await this.loadInitialData();
        this.loading = false;
    },
    
    methods: {
        async loadInitialData() {
            try {
                // Load kebele and sub-city data (only dynamic data needed)
                const kebeleResponse = await fetch('/api/method/education.education.api.get_kebele_subcity_data');
                if (!kebeleResponse.ok) {
                    const errorData = await kebeleResponse.json();
                    console.error('Failed to load kebele data:', errorData);
                    // Use fallback data if API fails
                    this.kebeleSubCityData = {
                        'Bole': ['Kebele 01', 'Kebele 02', 'Kebele 03'],
                        'Gadaa': ['Kebele 01', 'Kebele 02', 'Kebele 03'],
                        'Bokkuu': ['Kebele 01', 'Kebele 02', 'Kebele 03'],
                        'Luugoo': ['Kebele 01', 'Kebele 02', 'Kebele 03'],
                        'Dambalaa': ['Kebele 01', 'Kebele 02', 'Kebele 03'],
                        'Daabe': ['Kebele 01', 'Kebele 02', 'Kebele 03']
                    };
                    this.subCities = Object.keys(this.kebeleSubCityData);
                } else {
                    const kebeleData = await kebeleResponse.json();
                    this.kebeleSubCityData = kebeleData.message || {};
                    this.subCities = Object.keys(this.kebeleSubCityData);
                }
                
            } catch (error) {
                console.error('Error loading kebele data:', error);
                // Use fallback data if everything fails
                this.kebeleSubCityData = {
                    'Bole': ['Kebele 01', 'Kebele 02', 'Kebele 03'],
                    'Gadaa': ['Kebele 01', 'Kebele 02', 'Kebele 03'],
                    'Bokkuu': ['Kebele 01', 'Kebele 02', 'Kebele 03'],
                    'Luugoo': ['Kebele 01', 'Kebele 02', 'Kebele 03'],
                    'Dambalaa': ['Kebele 01', 'Kebele 02', 'Kebele 03'],
                    'Daabe': ['Kebele 01', 'Kebele 02', 'Kebele 03']
                };
                this.subCities = Object.keys(this.kebeleSubCityData);
            }
        },
        
        // File upload handling
        handleImageUpload(type, event) {
            const file = event.target.files[0];
            if (file) {
                // Validate file type
                const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
                if (!allowedTypes.includes(file.type)) {
                    this.showNotification('Please select a valid image file (JPG, PNG, GIF, WEBP)', 'error');
                    event.target.value = ''; // Clear the input
                    return;
                }
                
                // Validate file size (5MB max)
                if (file.size > 5 * 1024 * 1024) {
                    this.showNotification('File size must be less than 5MB', 'error');
                    event.target.value = ''; // Clear the input
                    return;
                }
                
                // Upload the file
                this.uploadAndAssignImage(type, file);
            }
        },
        
        async uploadAndAssignImage(type, file) {
            try {
                const fileUrl = await this.uploadFile(file);
                if (fileUrl) {
                    // Store the URL for session reuse if it's a parent image
                    if (type === 'father' || type === 'mother' || type === 'guardian') {
                        if (!this.sessionParentImages[type]) {
                            this.sessionParentImages[type] = fileUrl;
                        }
                    }
                    
                    // Assign to the appropriate data object
                    if (type === 'father') {
                        this.fatherData.image = fileUrl;
                    } else if (type === 'mother') {
                        this.motherData.image = fileUrl;
                    } else if (type === 'guardian') {
                        this.guardianData.image = fileUrl;
                    } else if (type === 'student') {
                        this.studentData.image = fileUrl;
                    }
                }
            } catch (error) {
                this.showNotification(`Failed to upload ${type} image: ${error.message}`, 'error');
            }
        },
        
        async uploadFile(file) {
            if (!file) return null;
            
            // Validate file before upload
            const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
            if (!allowedTypes.includes(file.type)) {
                this.showNotification('Please select a valid image file (JPG, PNG, GIF, WEBP)', 'error');
                return null;
            }
            
            if (file.size > 5 * 1024 * 1024) {
                this.showNotification('File size must be less than 5MB', 'error');
                return null;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            this.isUploadingFile = true;
            this.showNotification('Uploading image...', 'info');
            
            try {
                // Use only custom guest upload endpoint
                const response = await fetch('/api/method/education.education.api.upload_file_guest', {
                    method: 'POST',
                    body: formData,
                    credentials: 'include'
                });
                
                if (response.ok) {
                    const result = await response.json();
                    if (result.message && result.message.file_url) {
                        this.showNotification('Image uploaded successfully!', 'success');
                        return result.message.file_url;
                    } else {
                        this.showNotification('Upload failed: Invalid response format', 'error');
                        console.error('Upload response:', result);
                        return null;
                    }
                } else {
                    const errorText = await response.text();
                    let errorMessage = 'Upload failed';
                    
                    try {
                        const errorData = JSON.parse(errorText);
                        if (errorData.message) {
                            errorMessage = errorData.message;
                        } else if (errorData.exc) {
                            errorMessage = 'File upload error - please try again';
                        }
                    } catch (e) {
                        errorMessage = `Upload failed (${response.status})`;
                    }
                    
                    this.showNotification(errorMessage, 'error');
                    console.error('Upload response error:', response.status, response.statusText, errorText);
                    return null;
                }
            } catch (error) {
                console.error('File upload failed:', error);
                this.showNotification('Upload failed: Network error', 'error');
                return null;
            } finally {
                this.isUploadingFile = false;
            }
        },
        
        async handleStudentImageUpload(event) {
            const file = event.target.files[0];
            if (file) {
                const uploadedUrl = await this.uploadFile(file);
                if (uploadedUrl) {
                    this.studentData.image = uploadedUrl;
                }
            }
        },
        
        nextStep() {
            if (this.currentStep < this.totalSteps) {
                this.currentStep++;
            }
        },
        
        previousStep() {
            if (this.currentStep > 1) {
                this.currentStep--;
            }
        },
        
        async submitApplication() {
            // Validate the form first
            if (!this.validateForm()) {
                const errorCount = Object.keys(this.validationErrors).length;
                this.showNotification(`Please fix ${errorCount} validation error${errorCount > 1 ? 's' : ''} before submitting`, 'error');
                return;
            }
            
            this.isSubmitting = true;
            this.showNotification('Submitting application...', 'info');
            
            try {
                // Check for duplicate applications
                const checkResponse = await fetch('/api/method/education.education.api.check_duplicate_application', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        email: this.studentData.student_email_id,
                        mobile: this.guardianType === 'parent' ? this.fatherData.mobile_number : this.guardianData.mobile_number
                    })
                });
                
                if (checkResponse.ok) {
                    const checkData = await checkResponse.json();
                    if (checkData.message && checkData.message.exists) {
                        this.showNotification('An application with this email or mobile number already exists', 'error');
                        this.isSubmitting = false;
                        return;
                    }
                }

                // Create guardians first
                const guardians = [];
                
                if (this.guardianType === 'parent') {
                    // Create father guardian
                    console.log('Creating father guardian with data:', this.fatherData);
                    
                    // Upload father's photo if provided or reuse from session
                    let fatherPhotoUrl = this.sessionParentImages.father;
                    if (this.fatherData.photo && (!fatherPhotoUrl || this.fatherData.photo !== fatherPhotoUrl)) {
                        fatherPhotoUrl = await this.uploadFile(this.fatherData.photo);
                        this.sessionParentImages.father = fatherPhotoUrl;
                    }
                    
                    // Prepare father data for API (exclude photo field, add image URL)
                    const fatherDataForAPI = { ...this.fatherData };
                    delete fatherDataForAPI.photo;
                    if (fatherPhotoUrl) {
                        fatherDataForAPI.image = fatherPhotoUrl;
                    }
                    
                    const fatherResponse = await fetch('/api/method/education.education.api.create_guardian', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            guardian_data: fatherDataForAPI
                        })
                    });
                    
                    if (!fatherResponse.ok) {
                        const errorData = await fatherResponse.json();
                        throw new Error(`Failed to create father guardian: ${errorData.message || errorData.exc || fatherResponse.statusText}`);
                    }
                    
                    const fatherData = await fatherResponse.json();
                    
                    if (fatherData.message) {
                        guardians.push({
                            guardian: fatherData.message,
                            guardian_name: this.fatherData.guardian_name,
                            relation: 'Father'
                        });
                    } else {
                        throw new Error(`Failed to get father guardian ID: ${fatherData.exc || 'Unknown error'}`);
                    }
                    
                    // Create mother guardian
                    console.log('Creating mother guardian with data:', this.motherData);
                    
                    // Upload mother's photo if provided or reuse from session
                    let motherPhotoUrl = this.sessionParentImages.mother;
                    if (this.motherData.photo && (!motherPhotoUrl || this.motherData.photo !== motherPhotoUrl)) {
                        motherPhotoUrl = await this.uploadFile(this.motherData.photo);
                        this.sessionParentImages.mother = motherPhotoUrl;
                    }
                    
                    // Prepare mother data for API (exclude photo field, add image URL)
                    const motherDataForAPI = { ...this.motherData };
                    delete motherDataForAPI.photo;
                    if (motherPhotoUrl) {
                        motherDataForAPI.image = motherPhotoUrl;
                    }
                    
                    const motherResponse = await fetch('/api/method/education.education.api.create_guardian', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            guardian_data: motherDataForAPI
                        })
                    });
                    
                    if (!motherResponse.ok) {
                        const errorData = await motherResponse.json();
                        throw new Error(`Failed to create mother guardian: ${errorData.message || errorData.exc || motherResponse.statusText}`);
                    }
                    
                    const motherData = await motherResponse.json();
                    
                    if (motherData.message) {
                        guardians.push({
                            guardian: motherData.message,
                            guardian_name: this.motherData.guardian_name,
                            relation: 'Mother'
                        });
                    } else {
                        throw new Error(`Failed to get mother guardian ID: ${motherData.exc || 'Unknown error'}`);
                    }
                } else {
                    // Create guardian
                    console.log('Creating guardian with data:', this.guardianData);
                    
                    // Upload guardian's photo if provided or reuse from session
                    let guardianPhotoUrl = this.sessionParentImages.guardian;
                    if (this.guardianData.photo && (!guardianPhotoUrl || this.guardianData.photo !== guardianPhotoUrl)) {
                        guardianPhotoUrl = await this.uploadFile(this.guardianData.photo);
                        this.sessionParentImages.guardian = guardianPhotoUrl;
                    }
                    
                    // Prepare guardian data for API (exclude photo field, add image URL)
                    const guardianDataForAPI = { ...this.guardianData };
                    delete guardianDataForAPI.photo;
                    if (guardianPhotoUrl) {
                        guardianDataForAPI.image = guardianPhotoUrl;
                    }
                    
                    const guardianResponse = await fetch('/api/method/education.education.api.create_guardian', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            guardian_data: guardianDataForAPI
                        })
                    });
                    
                    if (!guardianResponse.ok) {
                        const errorData = await guardianResponse.json();
                        throw new Error(`Failed to create guardian: ${errorData.message || errorData.exc || guardianResponse.statusText}`);
                    }
                    
                    const guardianData = await guardianResponse.json();
                    
                    if (guardianData.message) {
                        guardians.push({
                            guardian: guardianData.message,
                            guardian_name: this.guardianData.guardian_name,
                            relation: 'Others'
                        });
                    } else {
                        throw new Error(`Failed to get guardian ID: ${guardianData.exc || 'Unknown error'}`);
                    }
                }
                
                // Generate school ID for new students
                let schoolId = '';
                if (this.studentType === 'new') {
                    const schoolIdResponse = await fetch('/api/method/education.education.api.generate_school_id', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            branch: this.branchSelection
                        })
                    });
                    
                    if (!schoolIdResponse.ok) {
                        const errorData = await schoolIdResponse.json();
                        throw new Error(`Failed to generate school ID: ${errorData.message || errorData.exc || schoolIdResponse.statusText}`);
                    }
                    
                    const schoolIdData = await schoolIdResponse.json();
                    if (schoolIdData.message) {
                        schoolId = schoolIdData.message;
                    } else {
                        throw new Error(`Failed to get school ID: ${schoolIdData.exc || 'Unknown error'}`);
                    }
                }
                
                // Upload student's photo if provided
                let studentPhotoUrl = null;
                if (this.studentData.image) {
                    studentPhotoUrl = await this.uploadFile(this.studentData.image);
                }
                
                // Prepare application data
                const applicationData = {
                    ...this.studentData,
                    custom_school_id: schoolId,
                    guardians: guardians,
                    siblings: []
                };
                
                // Add student image URL if uploaded
                if (studentPhotoUrl) {
                    applicationData.image = studentPhotoUrl;
                }
                
                // Create application
                const applicationResponse = await fetch('/api/method/education.education.api.create_student_application', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        application_data: applicationData
                    })
                });
                
                if (!applicationResponse.ok) {
                    const errorData = await applicationResponse.json();
                    throw new Error(`Failed to create application: ${errorData.message || errorData.exc || applicationResponse.statusText}`);
                }
                
                const applicationResult = await applicationResponse.json();
                
                if (applicationResult.message) {
                    this.submittedApplicationId = applicationResult.message;
                    this.showSuccessModal = true;
                } else {
                    throw new Error(`Failed to create application: ${applicationResult.exc || 'Unknown error'}`);
                }
                
            } catch (error) {
                console.error('Error submitting application:', error);
                
                // Show detailed error message
                let errorMessage = 'Error submitting application: ';
                if (error.message) {
                    errorMessage += error.message;
                } else {
                    errorMessage += 'Unknown error occurred. Please try again.';
                }
                
                alert(errorMessage);
                
                // Log detailed error for debugging
                console.log('Detailed error information:', {
                    message: error.message,
                    stack: error.stack,
                    name: error.name
                });
            } finally {
                this.isSubmitting = false;
            }
        },
        
        addSibling() {
            // Save current application to sessionApplications
            this.sessionApplications.push({
                guardianType: this.guardianType,
                fatherData: { ...this.fatherData, image: this.sessionParentImages.father },
                motherData: { ...this.motherData, image: this.sessionParentImages.mother },
                guardianData: { ...this.guardianData, image: this.sessionParentImages.guardian },
                studentData: { ...this.studentData },
                submittedApplicationId: this.submittedApplicationId,
                studentType: this.studentType,
                branchSelection: this.branchSelection
            });
            // Download PDF for current child
            this.finishAndDownload(true);
            // Pre-fill parent images for next child
            this.fatherData.photo = this.sessionParentImages.father;
            this.motherData.photo = this.sessionParentImages.mother;
            this.guardianData.photo = this.sessionParentImages.guardian;
            // ... existing code to reset studentData and go to next step ...
            this.studentData = {
                first_name: '',
                middle_name: '',
                last_name: '',
                gender: '',
                date_of_birth: '',
                program: '',
                primary_mobile_number: '',
                nationality: 'Ethiopian',
                academic_year: '2018 E.C.',
                custom_school_id: '',
                address_line_1: '',
                kebele: '',
                sub_city: '',
                city: 'Adama',
                state: 'Oromia',
                pincode: '',
                country: 'Ethiopia'
            };
            this.currentStep = 4;
            this.studentType = 'new';
            this.branchSelection = 'M1';
        },
        
        resetForm() {
            this.showSuccessModal = false;
            this.currentStep = 1;
            this.guardianType = 'parent';
            this.studentType = 'new';
            this.branchSelection = 'M1';
            this.submittedApplicationId = '';
            
            // Reset all form data
            this.fatherData = {
                guardian_name: '',
                email_address: '',
                mobile_number: '',
                alternate_number: '',
                education: '',
                occupation: '',
                work_address: '',
                education_other: '',
                occupation_other: ''
            };
            
            this.motherData = {
                guardian_name: '',
                email_address: '',
                mobile_number: '',
                alternate_number: '',
                education: '',
                occupation: '',
                work_address: '',
                education_other: '',
                occupation_other: ''
            };
            
            this.guardianData = {
                guardian_name: '',
                email_address: '',
                mobile_number: '',
                alternate_number: '',
                education: '',
                occupation: '',
                work_address: '',
                education_other: '',
                occupation_other: ''
            };
            
            this.studentData = {
                first_name: '',
                middle_name: '',
                last_name: '',
                gender: '',
                date_of_birth: '',
                program: '',
                primary_mobile_number: '',
                nationality: 'Ethiopian',
                academic_year: '2018 E.C.',
                custom_school_id: '',
                address_line_1: '',
                kebele: '',
                sub_city: '',
                city: 'Adama',
                state: 'Oromia',
                pincode: '',
                country: 'Ethiopia'
            };
            
            this.validationErrors = {};
            this.phoneErrors = {}; // Reset phone errors
            this.availableKebeles = []; // Reset kebele options
        },
        
        // Notification system
        showNotification(message, type = 'info', duration = 5000) {
            const id = Date.now();
            const notification = { id, message, type };
            this.notifications.push(notification);
            
            setTimeout(() => {
                this.removeNotification(id);
            }, duration);
        },
        
        removeNotification(id) {
            const index = this.notifications.findIndex(n => n.id === id);
            if (index !== -1) {
                this.notifications.splice(index, 1);
            }
        },
        
        // Email validation
        validateEmail(email) {
            if (!email) return false;
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return emailRegex.test(email);
        },
        
        // Enhanced school ID lookup with loading state
        async lookupStudent() {
            if (!this.existingSchoolId) {
                this.existingStudent = null;
                this.schoolIdError = '';
                return;
            }
            
            this.isCheckingSchoolId = true;
            this.schoolIdError = '';
            
            try {
                const response = await fetch('/api/method/education.education.api.search_student_by_school_id', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        school_id: this.existingSchoolId
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                if (data.message) {
                    this.existingStudent = data.message;
                    this.schoolIdError = '';
                    // Pre-fill student data
                    this.studentData.first_name = data.message.first_name || '';
                    this.studentData.middle_name = data.message.middle_name || '';
                    this.studentData.last_name = data.message.last_name || '';
                    this.studentData.custom_school_id = data.message.custom_school_id;
                    this.showNotification('Student found successfully!', 'success');
                } else {
                    this.existingStudent = null;
                    this.schoolIdError = 'Student not found with this school ID';
                    this.showNotification('Student not found with this school ID', 'error');
                }
            } catch (error) {
                console.error('Error looking up student:', error);
                this.existingStudent = null;
                this.schoolIdError = 'Error connecting to server. Please try again.';
                this.showNotification('Error looking up student. Please try again.', 'error');
            } finally {
                this.isCheckingSchoolId = false;
            }
        },
        
        // Enhanced form validation
        validateForm() {
            const errors = {};
            
            // Validate guardian information
            if (this.guardianType === 'parent') {
                // Father validation
                if (!this.fatherData.guardian_name) {
                    errors.father_name = 'Father\'s name is required';
                }
                if (!this.fatherData.mobile_number) {
                    errors.father_mobile = 'Father\'s mobile number is required';
                } else if (!/^9\d{8}$/.test(this.fatherData.mobile_number)) {
                    errors.father_mobile = 'Father\'s mobile number must be 9 digits starting with 9';
                }
                if (this.fatherData.email_address && !this.validateEmail(this.fatherData.email_address)) {
                    errors.father_email = 'Father\'s email address is invalid';
                }
                
                // Mother validation
                if (!this.motherData.guardian_name) {
                    errors.mother_name = 'Mother\'s name is required';
                }
                if (!this.motherData.mobile_number) {
                    errors.mother_mobile = 'Mother\'s mobile number is required';
                } else if (!/^9\d{8}$/.test(this.motherData.mobile_number)) {
                    errors.mother_mobile = 'Mother\'s mobile number must be 9 digits starting with 9';
                }
                if (this.motherData.email_address && !this.validateEmail(this.motherData.email_address)) {
                    errors.mother_email = 'Mother\'s email address is invalid';
                }
            } else {
                // Guardian validation
                if (!this.guardianData.guardian_name) {
                    errors.guardian_name = 'Guardian\'s name is required';
                }
                if (!this.guardianData.mobile_number) {
                    errors.guardian_mobile = 'Guardian\'s mobile number is required';
                } else if (!/^9\d{8}$/.test(this.guardianData.mobile_number)) {
                    errors.guardian_mobile = 'Guardian\'s mobile number must be 9 digits starting with 9';
                }
                if (this.guardianData.email_address && !this.validateEmail(this.guardianData.email_address)) {
                    errors.guardian_email = 'Guardian\'s email address is invalid';
                }
            }
            
            // Student validation
            if (!this.studentData.first_name) {
                errors.student_first_name = 'Student\'s first name is required';
            }
            if (!this.studentData.last_name) {
                errors.student_last_name = 'Student\'s last name is required';
            }
            if (!this.studentData.date_of_birth) {
                errors.student_dob = 'Student\'s date of birth is required';
            }
            if (!this.studentData.student_email_id) {
                errors.student_email = 'Student/Parent email is required';
            } else if (!this.validateEmail(this.studentData.student_email_id)) {
                errors.student_email = 'Student/Parent email address is invalid';
            }
            if (!this.studentData.program) {
                errors.student_program = 'Grade/Program is required';
            }
            if (!this.studentData.image) {
                errors.student_image = 'Student photo is required';
            }
            
            // Address validation
            if (!this.studentData.address_line_1) {
                errors.address = 'Home address is required';
            }
            if (!this.studentData.sub_city) {
                errors.sub_city = 'Sub-city is required';
            }
            if (!this.studentData.kebele) {
                errors.kebele = 'Kebele is required';
            }
            
            this.validationErrors = errors;
            return Object.keys(errors).length === 0;
        },
        
        getSelectedProgramName() {
            const program = this.programs.find(p => p.name === this.studentData.program);
            return program ? program.program_name : this.studentData.program;
        },

        // New methods for phone validation and education/occupation handling
        async validatePhone(guardianType, phone) {
            // Check if this is an alternate number field
            const isAlternateNumber = guardianType.includes('_alt');
            
            if (!phone) {
                if (isAlternateNumber) {
                    // Alternate numbers are optional, clear any existing error
                    this.phoneErrors[guardianType] = '';
                } else {
                    // Primary mobile numbers are required
                    this.phoneErrors[guardianType] = 'Mobile number is required';
                }
                return;
            }
            
            try {
                const response = await fetch('/api/method/education.education.api.validate_phone_number', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        phone_number: phone
                    })
                });
                
                if (!response.ok) {
                    console.error('Phone validation API error:', response.status, response.statusText);
                    this.phoneErrors[guardianType] = 'Error validating phone number';
                    return;
                }
                
                const data = await response.json();
                if (data.message && data.message.valid) {
                    this.phoneErrors[guardianType] = '';
                } else {
                    this.phoneErrors[guardianType] = data.message ? data.message.message : 'Error validating phone number';
                }
            } catch (error) {
                console.error('Error validating phone:', error);
                this.phoneErrors[guardianType] = 'Error validating phone number';
            }
        },

        handleEducationChange(guardianType, value) {
            const guardianData = this.getGuardianData(guardianType);
            if (value !== 'Other') {
                guardianData.education_other = '';
            }
        },

        handleOccupationChange(guardianType, value) {
            const guardianData = this.getGuardianData(guardianType);
            if (value !== 'Other') {
                guardianData.occupation_other = '';
            }
        },

        getGuardianData(guardianType) {
            if (guardianType === 'father') return this.fatherData;
            if (guardianType === 'mother') return this.motherData;
            return this.guardianData;
        },

        getGuardianName(guardianType) {
            if (guardianType === 'father') return 'Father';
            if (guardianType === 'mother') return 'Mother';
            return 'Guardian';
        },

        onSubCityChange() {
            // Reset kebele when sub-city changes
            this.studentData.kebele = '';
            // Update available kebeles based on selected sub-city
            this.availableKebeles = this.kebeleSubCityData[this.studentData.sub_city] || [];
        },
        
        async finishAndDownload(isSibling = false) {
            try {
                let applications = this.sessionApplications;
                if (!isSibling) {
                    // Add current application if finishing
                    applications = [...this.sessionApplications, {
                        guardianType: this.guardianType,
                        fatherData: { ...this.fatherData, image: this.sessionParentImages.father },
                        motherData: { ...this.motherData, image: this.sessionParentImages.mother },
                        guardianData: { ...this.guardianData, image: this.sessionParentImages.guardian },
                        studentData: { ...this.studentData },
                        submittedApplicationId: this.submittedApplicationId,
                        studentType: this.studentType,
                        branchSelection: this.branchSelection
                    }];
                }
                const response = await fetch('/api/method/education.education.api.generate_application_pdf', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        session_applications: applications
                    })
                });
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'student_application.pdf';
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    this.showSuccessModal = false;
                    if (!isSibling) this.resetForm();
                } else {
                    console.error('PDF generation failed');
                    alert('Error generating PDF. Please try again.');
                }
            } catch (error) {
                console.error('Error generating PDF:', error);
                alert('Error generating PDF. Please try again.');
            }
        }
    }
}).mount('#app'); 