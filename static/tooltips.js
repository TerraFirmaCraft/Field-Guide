window.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(tooltipToggleEl => {
    new bootstrap.Tooltip(tooltipToggleEl)
  })
})
