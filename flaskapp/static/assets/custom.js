function copyToClipboard(msg) {
    const tooltip = bootstrap.Tooltip.getInstance('#clipboard-button') // Returns a Bootstrap tooltip instance
    // setContent example
    tooltip.setContent({ '.tooltip-inner': 'Copied!' })
    navigator.clipboard.writeText(msg)
}

document.getElementById('bd-theme').addEventListener('click',()=>{
    if (document.documentElement.getAttribute('data-bs-theme') == 'dark') {
        document.documentElement.setAttribute('data-bs-theme','light')
    }
    else {
        document.documentElement.setAttribute('data-bs-theme','dark')
    }
})

var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
  return new bootstrap.Tooltip(tooltipTriggerEl)
})

const tooltipEl = document.getElementById('clipboard-button') // Returns a Bootstrap tooltip instance
const tooltip = bootstrap.Tooltip.getOrCreateInstance(tooltipEl)
tooltipEl.addEventListener('hidden.bs.tooltip', () => {
    tooltip.setContent({ '.tooltip-inner': 'Copy to clipboard' })
})

tooltip.hide()
