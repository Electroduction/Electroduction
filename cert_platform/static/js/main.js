/**
 * AI CertPro - Main JavaScript
 * Handles form submissions, API interactions, and dynamic content
 */

// API Base URL
const API_BASE = '/api';

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeForms();
    loadProgramData();
    initializeSmoothScrolling();
});

/**
 * Initialize form handlers
 */
function initializeForms() {
    // Individual enrollment form
    const enrollmentForm = document.querySelector('.enrollment-form');
    if (enrollmentForm) {
        enrollmentForm.addEventListener('submit', handleEnrollment);
    }

    // Enterprise form
    const enterpriseForm = document.querySelector('.enterprise-form');
    if (enterpriseForm) {
        enterpriseForm.addEventListener('submit', handleEnterpriseRequest);
    }
}

/**
 * Handle individual student enrollment
 */
async function handleEnrollment(e) {
    e.preventDefault();

    const formData = new FormData(e.target);
    const data = {
        name: formData.get('name') || e.target.querySelector('input[type="text"]').value,
        email: formData.get('email') || e.target.querySelector('input[type="email"]').value,
        program_id: formData.get('program') || e.target.querySelector('select').value,
        prior_knowledge: {}
    };

    try {
        const response = await fetch(`${API_BASE}/enroll`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            showSuccessMessage('Enrollment successful! Check your email for next steps.');
            e.target.reset();

            // Redirect to student dashboard
            setTimeout(() => {
                window.location.href = `/student/${result.student_id}/dashboard`;
            }, 2000);
        } else {
            showErrorMessage('Enrollment failed. Please try again.');
        }
    } catch (error) {
        console.error('Enrollment error:', error);
        showErrorMessage('An error occurred. Please try again later.');
    }
}

/**
 * Handle enterprise demo requests
 */
async function handleEnterpriseRequest(e) {
    e.preventDefault();

    const formData = new FormData(e.target);
    const data = {
        company_name: formData.get('company') || e.target.querySelector('input[type="text"]').value,
        email: formData.get('email') || e.target.querySelector('input[type="email"]').value,
        employee_count: parseInt(formData.get('employees') || e.target.querySelector('input[type="number"]').value),
        needs: formData.get('needs') || e.target.querySelector('textarea').value
    };

    try {
        // In production, this would send to CRM or sales system
        console.log('Enterprise request:', data);

        showSuccessMessage('Thank you! Our team will contact you within 24 hours.');
        e.target.reset();
    } catch (error) {
        console.error('Enterprise request error:', error);
        showErrorMessage('An error occurred. Please email us at enterprise@aicertpro.com');
    }
}

/**
 * Load and display program data dynamically
 */
async function loadProgramData() {
    try {
        const response = await fetch(`${API_BASE}/programs`);
        const programs = await response.json();

        // Update program counts or other dynamic data
        console.log(`Loaded ${programs.length} programs`);
    } catch (error) {
        console.error('Error loading programs:', error);
    }
}

/**
 * Initialize smooth scrolling for navigation links
 */
function initializeSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();

            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);

            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

/**
 * Show success message
 */
function showSuccessMessage(message) {
    const messageDiv = createMessageElement(message, 'success');
    document.body.appendChild(messageDiv);

    setTimeout(() => {
        messageDiv.remove();
    }, 5000);
}

/**
 * Show error message
 */
function showErrorMessage(message) {
    const messageDiv = createMessageElement(message, 'error');
    document.body.appendChild(messageDiv);

    setTimeout(() => {
        messageDiv.remove();
    }, 5000);
}

/**
 * Create message element
 */
function createMessageElement(message, type) {
    const div = document.createElement('div');
    div.className = `message message-${type}`;
    div.textContent = message;

    div.style.position = 'fixed';
    div.style.top = '20px';
    div.style.right = '20px';
    div.style.padding = '1rem 2rem';
    div.style.borderRadius = '8px';
    div.style.color = 'white';
    div.style.fontWeight = '600';
    div.style.zIndex = '9999';
    div.style.boxShadow = '0 4px 12px rgba(0,0,0,0.2)';
    div.style.animation = 'slideIn 0.3s ease-out';

    if (type === 'success') {
        div.style.background = '#10b981';
    } else if (type === 'error') {
        div.style.background = '#ef4444';
    }

    return div;
}

/**
 * Workforce Gap Analysis Tool (for HR page)
 */
async function analyzeWorkforceGaps(currentSkills, requiredSkills) {
    try {
        const response = await fetch(`${API_BASE}/hr/workforce-analysis`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                current_skills: currentSkills,
                required_skills: requiredSkills
            })
        });

        const analysis = await response.json();
        return analysis;
    } catch (error) {
        console.error('Workforce analysis error:', error);
        return null;
    }
}

/**
 * Deploy training to employees (for HR dashboard)
 */
async function deployTraining(companyId, programIds, employeeIds, deadline) {
    try {
        const response = await fetch(`${API_BASE}/hr/deploy-training`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                company_id: companyId,
                program_ids: programIds,
                employee_ids: employeeIds,
                deadline: deadline
            })
        });

        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Training deployment error:', error);
        return null;
    }
}

/**
 * Submit lesson feedback
 */
async function submitFeedback(studentId, programId, lessonId, rating, comments) {
    try {
        const response = await fetch(`${API_BASE}/feedback`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                student_id: studentId,
                program_id: programId,
                lesson_id: lessonId,
                rating: rating,
                comments: comments,
                helpful: rating >= 3
            })
        });

        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Feedback submission error:', error);
        return null;
    }
}

/**
 * Get student progress
 */
async function getProgress(studentId) {
    try {
        const response = await fetch(`${API_BASE}/progress/${studentId}`);
        const progress = await response.json();
        return progress;
    } catch (error) {
        console.error('Error fetching progress:', error);
        return null;
    }
}

// Add CSS animation for messages
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);
