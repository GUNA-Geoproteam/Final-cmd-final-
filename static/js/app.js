/**
 * Toggles the visibility of the settings pop-up.
 */
function toggleSettingsPopup() {
  const popup = document.getElementById('settings-popup');
  popup.style.display = popup.style.display === 'block' ? 'none' : 'block';
}

/**
 * Handles the file upload form submission.
 * Sends the uploaded file and related data to the server for processing.
 */
async function submitForm() {
  const form = document.getElementById('upload-form'); // The file upload form
  const formData = new FormData(form); // Collect form data

  // UI Elements for displaying progress and results
  const progressContainer = document.getElementById('progress-container');
  const progressBar = document.getElementById('progress-bar');
  const responseDiv = document.getElementById('response');
  const messageSpan = document.getElementById('response-message');
  const totalRunsCell = document.getElementById('total-runs');
  const successCountCell = document.getElementById('success-count');
  const failureCountCell = document.getElementById('failure-count');

  // Reset UI elements for new submission
  progressContainer.style.display = 'block';
  progressBar.value = 0;
  responseDiv.style.display = 'none';

  try {
    // Send the form data to the server
    const response = await fetch('/process', {
      method: 'POST',
      body: formData,
    });

    // Parse the JSON response
    const data = await response.json();

    if (response.ok) {
      // Display success message and update result table
      responseDiv.style.display = 'block';
      messageSpan.textContent = data.message || "Processing completed.";

      if (data.summary) {
        totalRunsCell.textContent = data.summary.total_runs || 0;
        successCountCell.textContent = data.summary.success_count || 0;
        failureCountCell.textContent = data.summary.failure_count || 0;
      } else {
        messageSpan.textContent = "Processing completed, but no summary available.";
      }
    } else {
      // Handle errors returned by the server
      messageSpan.textContent = data.error || "An error occurred.";
    }
  } catch (error) {
    // Handle network or unexpected errors
    messageSpan.textContent = `An error occurred: ${error.message}`;
  }

  // Hide the progress bar after completion
  progressContainer.style.display = 'none';
}

/**
 * Opens the "Set Up Scheduled Reports" modal.
 * Hides the settings pop-up (if open) and displays the modal.
 */
function openModal() {

  resetScheduledReportsForm();
  document.getElementById('scheduled-reports-modal').style.display = 'flex';
  document.body.classList.add('modal-active'); // Add a class to indicate modal is active
}

function showNotification(message) {
  // Create a notification element
  const notification = document.createElement('div');
  notification.className = 'notification'; // Add a class for styling
  notification.textContent = message;

  // Add the notification to the body
  document.body.appendChild(notification);

  // Remove the notification after 5 seconds
  setTimeout(() => {
    notification.remove();
  }, 5000);
}

/**
 * Get the effective background color of an element (not transparent).
 * Traverses up the DOM tree if the background is transparent.
 */
function getEffectiveBackgroundColor(element) {
  let bgColor = window.getComputedStyle(element).backgroundColor;

  // Traverse up the DOM tree if the background is transparent
  while (bgColor === 'rgba(0, 0, 0, 0)' || bgColor === 'transparent') {
    element = element.parentElement;
    if (!element) {
      // Default to white if no parent has a background color
      return 'rgb(255, 255, 255)';
    }
    bgColor = window.getComputedStyle(element).backgroundColor;
  }

  return bgColor;
}

/**
 * Adjust label colors based on the effective background brightness.
 */
function adjustLabelColors() {
  const labels = document.querySelectorAll('label');

  labels.forEach((label) => {
    const bgColor = getEffectiveBackgroundColor(label.parentElement); // Get background
    const rgb = bgColor.match(/\d+/g);

    if (rgb && rgb.length >= 3) {
      const [r, g, b] = rgb.map(Number);

      // Calculate luminance (perceptual brightness)
      const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;

      // Apply text color: white for dark backgrounds, black for light backgrounds
      label.style.color = luminance < 128 ? 'white' : 'black';
    }
  });
}

// Call the function on page load
document.addEventListener('DOMContentLoaded', adjustLabelColors);

document.addEventListener('DOMContentLoaded', () => {
  // Get all frequency radio buttons and the custom days input field
  const frequencyRadios = document.querySelectorAll('input[name="frequency"]');
  const dayInputField = document.getElementById('day-input-field');

  // Add event listeners to each radio button
  frequencyRadios.forEach((radio) => {
    radio.addEventListener('change', (event) => {
      if (['fortnightly', 'monthly', 'custom'].includes(event.target.value)) {
        // Show the custom days input field
        dayInputField.style.display = 'block';
      } else {
        // Hide the custom days input field for other frequencies
        dayInputField.style.display = 'none';
      }
    });
  });
});


document.addEventListener('DOMContentLoaded', () => {
    const reportSelect = document.getElementById('report-select');

    // Fetch reports from the backend
    fetch('/get-reports')
        .then((response) => response.json())
        .then((data) => {
            if (data.reports) {
                // Clear existing options
                reportSelect.innerHTML = '';

                // Populate the dropdown
                data.reports.forEach((report) => {
                    const option = document.createElement('option');
                    option.value = report;
                    option.textContent = report;
                    reportSelect.appendChild(option);
                });
            } else if (data.error) {
                console.error('Error fetching reports:', data.error);
            }
        })
        .catch((error) => {
            console.error('Error:', error);
        });
});

document.getElementById('schedule-form').addEventListener('submit', async (event) => {
  event.preventDefault();

  const submitButton = document.querySelector('#schedule-form button[type="submit"]');
  submitButton.disabled = true; // prevent double submits

  // 1) Gather your multi-select and other fields
  const selectedReports = $('#report-select').val();
  const formData        = new FormData(event.target);

  // 2) Grab the new “Single vs Bulk” radio value
  const reportType = document.querySelector('input[name="report_type"]:checked').value;

  // 3) Build your JSON payload
  const payload = {
    reports:          selectedReports,
    report_type:      reportType,              // ← added
    frequency:        formData.get('frequency'),
    day:              formData.get('day'),
    custom_days:      formData.get('custom_days'),
    file_path:        formData.get('file_path'),
    recipients_email: formData.get('recipients_email'),
    date_filter:      formData.get('date_filter')  // if you’re capturing that too
  };

  // 4) POST it to your Flask endpoint
  try {
    const response = await fetch('/schedule-report', {
      method:  'POST',
      headers: {'Content-Type': 'application/json'},
      body:    JSON.stringify(payload),
    });
    const result = await response.json();

    if (response.ok) {
      showNotification('Reports scheduled successfully!');
      closeModal();
      fetchScheduledReports();  // refresh the table
    } else {
      alert(`Error: ${result.error || result.message}`);
    }
  } catch (err) {
    alert(`Network error: ${err.message}`);
  } finally {
    submitButton.disabled = false;
  }
});

function resetScheduledReportsForm() {
  const form = document.getElementById('schedule-form');
  form.reset(); // Resets all input fields to their default values

  // Reset multi-select dropdown (Select2)
  $('#report-select').val(null).trigger('change'); // Clear selected values in Select2

  // Hide the custom days input field
  const dayInputField = document.getElementById('day-input-field');
  if (dayInputField) {
    dayInputField.style.display = 'none';
  }
}



/**
 * Closes the "Set Up Scheduled Reports" modal.
 * Removes modal-active class and hides the settings pop-up.
 */
function closeModal() {
  const modal = document.getElementById('scheduled-reports-modal');
  modal.style.display = 'none';
  document.body.classList.remove('modal-active');

  // Ensure the settings pop-up is hidden
  const settingsPopup = document.getElementById('settings-popup');
  if (settingsPopup) {
    settingsPopup.style.display = 'none';
  }
}

/**
 * Toggles visibility of the weekly options based on the selected frequency.
 * Only displays the day selection if "Weekly" is chosen.
 */
document.querySelectorAll('input[name="frequency"]').forEach((radio) => {
  radio.addEventListener('change', (event) => {
    const weeklyOptions = document.getElementById('weekly-options');
    if (event.target.value === 'weekly') {
      weeklyOptions.style.display = 'block';
    } else {
      weeklyOptions.style.display = 'none';
    }
  });
});

/**
 * Handles the "Set Up Scheduled Reports" form submission.
 * Collects user input and sends it to the server for scheduling.
 */

document.getElementById('schedule-form').addEventListener('submit', async (event) => {
  event.preventDefault();

  // Fetch selected reports and form data
  const selectedReports = $('#report-select').val(); // Multi-select values
  const formData = new FormData(event.target);

  // Prepare payload
  const payload = {
    reports: selectedReports,
    frequency: formData.get('frequency'),
    day: formData.get('day'), // Optional (weekly only)
    custom_days: formData.get('custom_days'),
    file_path: formData.get('file_path'), // Report save path
    recipients_email: formData.get('recipients_email'), // Email recipients
  };

  try {
    // Send scheduling data to the server
    const response = await fetch('/schedule-report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (response.ok) {
      showNotification('Reports scheduled successfully!');
      closeModal();
    } else {
      const error = await response.json();
      alert(`Error: ${error.message}`);
    }
  } catch (error) {
    alert(`An error occurred: ${error.message}`);
  }
});


/**
 * Initializes Select2 for the multi-select dropdown.
 * Provides search and clear functionality for selecting reports.
 */
$(document).ready(function () {
  $('#report-select').select2({
    placeholder: "Select Reports",
    allowClear: true,
    width: '100%', // Ensure the dropdown fits within the parent container
  });
});

async function fetchScheduledReports() {
    try {
        const response = await fetch('/view-scheduled-reports');
        if (!response.ok) {
            throw new Error('Failed to load scheduled reports.');
        }

        const reports = await response.json();
        if (reports.error) {
            throw new Error(reports.error);
        }

        const tableBody = document.querySelector('#scheduled-reports-table tbody');
        tableBody.innerHTML = ''; // Clear existing rows

        reports.forEach((report, index) => {
            const row = document.createElement('tr');
            row.innerHTML = `
            <td>${report.customer_name}</td>
            <td>${report.report_name}</td>
            <td>${report.frequency}</td>
            <td>${report.day         || 'N/A'}</td>
            <td>${report.custom_days || 'N/A'}</td>
            <td>${report.file_path}</td>
            <td>${report.recipients_email}</td>
            <td>${report.report_type  || 'N/A'}</td>   <!-- ← new -->
             <td>
    <button class="delete-report-btn"
            data-customer="${report.customer_name}"
            data-report="${report.report_name}"
            data-frequency="${report.frequency}"
            data-type="${report.report_type}">    <!-- ← new -->
      Delete
    </button>
  </td>
`;
            tableBody.appendChild(row);
        });

        attachDeleteEventListeners();


        // Display the section
        document.getElementById('scheduled-reports-section').style.display = 'block';
    } catch (error) {
        console.error('Error fetching scheduled reports:', error);
        alert(`Failed to load scheduled reports: ${error.message}`);
    }
}

// Add functionality to handle "View Scheduled Reports" and delete actions.

document.addEventListener('DOMContentLoaded', () => {
    const viewScheduledReportsLink = document.getElementById('view-scheduled-reports-link');
    const scheduledReportsSection = document.getElementById('scheduled-reports-section');
    const reportsTableBody = document.getElementById('reports-table-body');

    // Hide scheduled reports section initially
    scheduledReportsSection.style.display = 'none';

    // Fetch and display scheduled reports
    viewScheduledReportsLink.addEventListener('click', async () => {
        try {
            const response = await fetch('/view-scheduled-reports');
            if (!response.ok) {
                throw new Error('Failed to load scheduled reports.');
            }

            const reports = await response.json();
            reportsTableBody.innerHTML = '';

            // Populate table rows dynamically
            reports.forEach((report) => {
                const row = document.createElement('tr');

                row.innerHTML = `
                    <td>${report.customer_name}</td>
                    <td>${report.report_name}</td>
                    <td>${report.frequency}</td>
                    <td>${report.day || '-'}</td>
                    <td>${report.custom_days || '-'}</td>
                    <td>${report.file_path}</td>
                    <td>${report.recipients_email}</td>
                    <td><button class="delete-report-btn" data-id="${report.id}">Delete</button></td>
                `;

                reportsTableBody.appendChild(row);
            });

            // Add delete event listeners
            document.querySelectorAll('.delete-report-btn').forEach((button) => {
                button.addEventListener('click', async (event) => {
                    const reportId = event.target.dataset.id;

                    try {
                        const deleteResponse = await fetch(`/delete-scheduled-report/${reportId}`, {
                            method: 'DELETE',
                        });

                        if (!deleteResponse.ok) {
                            throw new Error('Failed to delete the report.');
                        }

                        // Reload the reports table
                        viewScheduledReportsLink.click();
                    } catch (error) {
                        alert(`Error: ${error.message}`);
                    }
                });
            });

            scheduledReportsSection.style.display = 'block';
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    });

    // Close the scheduled reports section
    const closeScheduledReportsBtn = document.getElementById('close-scheduled-reports');
    closeScheduledReportsBtn.addEventListener('click', () => {
        scheduledReportsSection.style.display = 'none';
    });
});

// Delete a report
async function deleteScheduledReport(customerName, reportName, frequency) {
    if (confirm(`Are you sure you want to delete the report "${reportName}" for "${customerName}" - frequency "${frequency}"?`)) {
        try {
            const response = await fetch('/delete-scheduled-report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ customer_name: customerName, report_name: reportName, frequency: frequency }),
            });

            if (response.ok) {
                alert('Report deleted successfully!');
                await fetchScheduledReports();
            } else {
                const data = await response.json();
                alert(`Failed to delete the report: ${data.error}`);
            }
        } catch (error) {
            console.error('Error deleting report:', error);
            alert('An error occurred while deleting the report.');
        }
    }
}


function attachDeleteEventListeners() {
    document.querySelectorAll('.delete-report-btn').forEach(button => {
        button.addEventListener('click', event => {
            const customerName = event.target.dataset.customer;
            const reportName = event.target.dataset.report;
            const frequency = event.target.dataset.frequency;
            deleteScheduledReport(customerName, reportName, frequency);
        });
    });
}

function toggleScheduledReportsSection(show) {
    const section = document.getElementById('scheduled-reports-section');
    section.style.display = show ? 'block' : 'none';
}

document.getElementById('view-scheduled-reports').addEventListener('click', () => {
    toggleScheduledReportsSection(true);
    fetchScheduledReports();
});

document.getElementById('close-scheduled-reports').addEventListener('click', () => {
    toggleScheduledReportsSection(false);
});

// Close the scheduled reports section
function closeReportsSection() {
  document.getElementById('scheduled-reports-section').style.display = 'none';
}
// Function to open the Alignment Configuration Modal
async function openAlignmentConfig() {
  document.getElementById('alignment-config-modal').style.display = 'flex';
  try {
    const response = await fetch('/get-alignments');
    const alignments = await response.json();
    const reportSelect = document.getElementById('report-select-alignment');
    reportSelect.innerHTML = ''; // Clear any existing options

    // Populate drop-down with report names (keys of the alignment_dict)
    for (const reportName in alignments) {
      const option = document.createElement('option');
      option.value = reportName;
      option.textContent = reportName;
      reportSelect.appendChild(option);
    }

    // Add event listener for when a report is selected
    reportSelect.addEventListener('change', function() {
      const selectedReport = this.value;
      displayAlignmentTable(alignments[selectedReport]);
    });
  } catch (error) {
    console.error('Error fetching alignments:', error);
  }
}

// Function to render the editable alignment table
function displayAlignmentTable(alignmentData) {
  const container = document.getElementById('alignment-table-container');
  container.innerHTML = ''; // Clear previous content

  if (!alignmentData) {
    container.innerHTML = '<p>No alignment data available for the selected report.</p>';
    return;
  }

  // Create a table with headers
  const table = document.createElement('table');
  table.id = 'alignment-table';
  table.innerHTML = `
    <thead>
  <tr>
    <th>Customer Name</th>
    <th>Report Name</th>
    <th>Frequency</th>
    <th>Day</th>
    <th>Custom Days</th>
    <th>File Path</th>
    <th>Recipients Email</th>
    <th>Report Type</th>  <!-- ← new -->
    <th>Actions</th>
  </tr>
</thead>
  `;
  const tbody = table.querySelector('tbody');

  // Loop over alignmentData keys (columns)
  for (const col in alignmentData) {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${col}</td>
      <td contenteditable="true">${alignmentData[col].align}</td>
      <td contenteditable="true">${alignmentData[col].width}</td>
    `;
    tbody.appendChild(row);
  }
  container.appendChild(table);

  // Add a Save Changes button below the table
  const saveBtn = document.createElement('button');
  saveBtn.textContent = 'Save Changes';
  saveBtn.onclick = saveAlignmentChanges;
  container.appendChild(saveBtn);
}

async function saveAlignmentChanges() {
  const table = document.getElementById('alignment-table');
  const rows = table.querySelectorAll('tbody tr');
  const updatedData = {};

  rows.forEach(row => {
    const cells = row.querySelectorAll('td');
    const colNum = cells[0].textContent.trim();
    const alignValue = cells[1].textContent.trim();
    const widthValue = cells[2].textContent.trim();
    updatedData[colNum] = {
      align: alignValue,
      width: parseInt(widthValue, 10) || widthValue
    };
  });

  // Get the currently selected report from the drop-down
  const reportName = document.getElementById('report-select-alignment').value;
  const payload = {
    report: reportName,
    data: updatedData
  };

  // Debug log: Check the payload before sending
  console.log("Saving alignment changes for report:", reportName, payload);

  try {
    const response = await fetch('/update-alignments', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (response.ok) {
      alert('Alignment updated successfully!');
      // Re-fetch and log new alignments for debugging
      fetch('/get-alignments')
        .then(res => res.json())
        .then(updatedAlignments => console.log("Updated alignments:", updatedAlignments));
    } else {
      alert('Failed to update alignment.');
    }
  } catch (error) {
    alert('Error updating alignment: ' + error.message);
  }
}


// Function to close the Alignment Configuration Modal
function closeAlignmentModal() {
  document.getElementById('alignment-config-modal').style.display = 'none';
}