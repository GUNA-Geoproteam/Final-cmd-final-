/**
 * Initializes a WebSocket connection using Socket.IO.
 * Enables real-time communication between the server and client.
 */
const socket = io('/');

/**
 * Listens for 'progress_update' events from the server.
 * Updates the progress bar and its value displayed on the UI based on the received data.
 *
 * @param {Object} data - The progress update data received from the server.
 * @param {number} data.progress - The current progress percentage (0-100).
 */
socket.on('progress_update', (data) => {
  // Get progress bar and value elements from the DOM
  const progressBar = document.getElementById('progress-bar');
  const progressValue = document.getElementById('progress-value');

  // Update progress bar and displayed percentage if data is valid
  if (progressBar && data.progress !== undefined) {
    progressBar.value = data.progress; // Set progress bar value
    if (progressValue) {
      progressValue.textContent = `Progress: ${data.progress}%`; // Update progress text
    }
  }
});

/**
 * Listens for any event received via the WebSocket connection.
 * Logs the event name and data to the console for debugging purposes.
 *
 * @param {string} event - The name of the received event.
 * @param {Object} data - The data payload associated with the event.
 */
socket.onAny((event, data) => {
  console.log(`Received event: ${event}`, data); // Log event name and data
});
