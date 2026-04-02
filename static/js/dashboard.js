let clientsData = [];
let currentEstimatedCalories = 0;


const clientForm = document.getElementById('clientForm');
const adherenceSlider = document.getElementById('clientAdherence');
const adherenceValue = document.getElementById('adherenceValue');
const programSelect = document.getElementById('clientProgram');
const weightInput = document.getElementById('clientWeight');
const workoutPlan = document.getElementById('workoutPlan');
const dietPlan = document.getElementById('dietPlan');
const calorieDisplay = document.getElementById('calorieDisplay');
const clientTableBody = document.getElementById('clientTableBody');
const clientCount = document.getElementById('clientCount');
const messageContainer = document.getElementById('messageContainer');
const chartContainer = document.getElementById('chartContainer');


document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    loadClients();
});

function initializeEventListeners() {
    adherenceSlider.addEventListener('input', function() {
        adherenceValue.textContent = this.value;
    });

    programSelect.addEventListener('change', function() {
        updateProgramDetails();
        updateCalorieEstimate();
    });

    weightInput.addEventListener('input', updateCalorieEstimate);

    clientForm.addEventListener('submit', function(e) {
        e.preventDefault();
        saveClient();
    });
}

function updateProgramDetails() {
    const selectedProgram = programSelect.value;

    if (!selectedProgram || !programs[selectedProgram]) {
        workoutPlan.textContent = 'Select a program to view training plan...';
        dietPlan.textContent = 'Select a program to view nutrition plan...';
        workoutPlan.className = 'program-content';
        dietPlan.className = 'program-content';
        return;
    }

    const programData = programs[selectedProgram];

    workoutPlan.textContent = programData.workout;
    workoutPlan.className = `program-content ${getProgramClass(selectedProgram)}`;

    dietPlan.textContent = programData.diet;
    dietPlan.className = 'program-content';
}

function getProgramClass(programName) {
    const classMap = {
        'Fat Loss (FL)': 'fat-loss',
        'Muscle Gain (MG)': 'muscle-gain',
        'Beginner (BG)': 'beginner'
    };
    return classMap[programName] || '';
}

function updateCalorieEstimate() {
    const weight = parseFloat(weightInput.value);
    const selectedProgram = programSelect.value;

    if (!weight || !selectedProgram || !programs[selectedProgram]) {
        calorieDisplay.innerHTML = '<i class="fas fa-fire"></i> Estimated Calories: --';
        currentEstimatedCalories = 0;
        return;
    }

    const programData = programs[selectedProgram];
    const estimatedCalories = Math.round(weight * programData.calorie_factor);
    currentEstimatedCalories = estimatedCalories;

    calorieDisplay.innerHTML = `<i class="fas fa-fire"></i> Estimated Calories: ${estimatedCalories} kcal`;
}

async function saveClient() {
    const formData = new FormData(clientForm);
    const clientData = Object.fromEntries(formData);

    try {
        showSpinner(true);

        const response = await fetch('/add-client', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(clientData)
        });

        const result = await response.json();

        if (result.success) {
            showMessage('success', result.message);
            clientForm.reset();
            adherenceValue.textContent = '0';
            updateProgramDetails();
            updateCalorieEstimate();
            await loadClients();
            await updateChart();
        } else {
            showMessage('error', result.error);
        }
    } catch (error) {
        showMessage('error', 'Failed to save client: ' + error.message);
    } finally {
        showSpinner(false);
    }
}

async function loadClients() {
    try {
        const response = await fetch('/clients');
        const result = await response.json();

        if (result.success) {
            clientsData = result.clients;
            updateClientTable();
            updateClientCount();
        } else {
            console.error('Failed to load clients:', result.error);
        }
    } catch (error) {
        console.error('Error loading clients:', error);
    }
}

function updateClientTable() {
    if (clientsData.length === 0) {
        clientTableBody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-muted">
                    No clients added yet...
                </td>
            </tr>
        `;
        return;
    }

    clientTableBody.innerHTML = clientsData.map(client => `
        <tr class="client-row-new">
            <td>
                <strong>${escapeHtml(client.name)}</strong>
            </td>
            <td>${client.age}</td>
            <td>${client.weight} kg</td>
            <td>
                <span class="badge" style="background-color: ${programs[client.program]?.color || '#666'}">
                    ${client.program}
                </span>
            </td>
            <td>
                <span class="badge adherence-badge ${getAdherenceClass(client.adherence)}">
                    ${client.adherence}%
                </span>
            </td>
            <td>
                <strong>${client.estimated_calories} kcal</strong>
            </td>
            <td>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteClient(${client.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

function getAdherenceClass(adherence) {
    if (adherence >= 80) return 'adherence-high';
    if (adherence >= 60) return 'adherence-medium';
    return 'adherence-low';
}

function updateClientCount() {
    clientCount.textContent = clientsData.length;
}

async function deleteClient(clientId) {
    if (!confirm('Are you sure you want to delete this client?')) {
        return;
    }

    try {
        showSpinner(true);

        const response = await fetch(`/delete-client/${clientId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            showMessage('success', result.message);
            await loadClients();
            await updateChart();
        } else {
            showMessage('error', result.error);
        }
    } catch (error) {
        showMessage('error', 'Failed to delete client: ' + error.message);
    } finally {
        showSpinner(false);
    }
}

async function updateChart() {
    try {
        const response = await fetch('/progress-chart');
        const result = await response.json();

        if (result.success) {
            chartContainer.innerHTML = `
                <img src="${result.chart_data}" alt="Progress Chart" class="img-fluid">
            `;
        } else {
            chartContainer.innerHTML = `
                <p class="text-muted">
                    <i class="fas fa-chart-bar"></i> 
                    ${result.error || 'Add clients to see progress chart...'}
                </p>
            `;
        }
    } catch (error) {
        console.error('Error updating chart:', error);
        chartContainer.innerHTML = `
            <p class="text-danger">
                <i class="fas fa-exclamation-triangle"></i> 
                Failed to load chart
            </p>
        `;
    }
}

async function exportCSV() {
    if (clientsData.length === 0) {
        showMessage('warning', 'No clients to export');
        return;
    }

    try {
        showSpinner(true);

        const response = await fetch('/export-csv');

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `aceest_clients_${new Date().toISOString().slice(0, 10)}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            showMessage('success', 'Client data exported successfully');
        } else {
            const result = await response.json();
            showMessage('error', result.error || 'Export failed');
        }
    } catch (error) {
        showMessage('error', 'Failed to export CSV: ' + error.message);
    } finally {
        showSpinner(false);
    }
}

function resetForm() {
    clientForm.reset();
    adherenceValue.textContent = '0';
    updateProgramDetails();
    updateCalorieEstimate();
    showMessage('info', 'Form has been reset');
}

async function resetAllClients() {
    if (!confirm('Are you sure you want to delete ALL clients? This cannot be undone!')) {
        return;
    }

    try {
        showSpinner(true);

        const response = await fetch('/reset-clients', {
            method: 'POST'
        });

        const result = await response.json();

        if (result.success) {
            showMessage('success', result.message);
            await loadClients();
            await updateChart();
        } else {
            showMessage('error', result.error || 'Reset failed');
        }
    } catch (error) {
        showMessage('error', 'Failed to reset clients: ' + error.message);
    } finally {
        showSpinner(false);
    }
}

function showSpinner(show) {
    const spinner = document.getElementById('loadingSpinner');
    if (show) {
        spinner.classList.remove('d-none');
    } else {
        spinner.classList.add('d-none');
    }
}

function showMessage(type, message) {
    const alertTypes = {
        success: 'alert-success',
        error: 'alert-danger',
        warning: 'alert-warning',
        info: 'alert-info'
    };

    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-triangle',
        warning: 'fas fa-exclamation-circle',
        info: 'fas fa-info-circle'
    };

    const alertHtml = `
        <div class="alert ${alertTypes[type]} alert-dismissible fade show" role="alert">
            <i class="${icons[type]}"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    messageContainer.innerHTML = alertHtml;

    if (type === 'success') {
        setTimeout(() => {
            const alert = messageContainer.querySelector('.alert');
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 3000);
    }
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        if (document.getElementById('clientName').value.trim()) {
            saveClient();
        }
    }

    if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
        e.preventDefault();
        resetForm();
    }

    if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
        e.preventDefault();
        exportCSV();
    }
});

function autoSaveForm() {
    const formData = new FormData(clientForm);
    const data = Object.fromEntries(formData);
    localStorage.setItem('aceest_form_draft', JSON.stringify(data));
}

function loadFormDraft() {
    const draft = localStorage.getItem('aceest_form_draft');
    if (draft) {
        try {
            const data = JSON.parse(draft);
            Object.keys(data).forEach(key => {
                const element = document.querySelector(`[name="${key}"]`);
                if (element && data[key]) {
                    element.value = data[key];
                    if (key === 'adherence') {
                        adherenceValue.textContent = data[key];
                    }
                }
            });
            updateProgramDetails();
            updateCalorieEstimate();
        } catch (e) {
            console.error('Error loading form draft:', e);
        }
    }
}


function clearFormDraft() {
    localStorage.removeItem('aceest_form_draft');
}