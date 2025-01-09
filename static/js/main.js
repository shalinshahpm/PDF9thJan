// File upload handling
function initializeFileUpload() {
    const dropZone = document.getElementById('drop-zone');
    if (!dropZone) return;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        dropZone.classList.add('highlight');
    }

    function unhighlight(e) {
        dropZone.classList.remove('highlight');
    }

    dropZone.addEventListener('drop', handleDrop, false);
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
}

function handleFiles(files) {
    const formData = new FormData();
    [...files].forEach(file => formData.append('files[]', file));

    const progressBar = document.querySelector('.progress-bar');
    progressBar.style.width = '0%';
    progressBar.classList.remove('d-none');

    fetch('/pdf/merge', {
        method: 'POST',
        body: formData
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'processed.pdf';
        document.body.appendChild(a);
        a.click();
        a.remove();
        progressBar.classList.add('d-none');
    })
    .catch(error => {
        console.error('Error:', error);
        progressBar.classList.add('d-none');
    });
}

// Stripe integration
let stripe;

async function initializeStripe() {
    // Get the publishable key from the server
    const response = await fetch('/subscription/config');
    const {publishableKey} = await response.json();
    stripe = Stripe(publishableKey);

    const buttons = document.querySelectorAll('.subscribe-button');
    buttons.forEach(button => {
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            const priceId = button.getAttribute('data-price-id');

            try {
                // Show loading state
                button.disabled = true;
                button.textContent = 'Processing...';

                const response = await fetch('/subscription/create-checkout-session', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `price_id=${priceId}`
                });

                const session = await response.json();

                if (session.error) {
                    throw new Error(session.error);
                }

                const result = await stripe.redirectToCheckout({
                    sessionId: session.sessionId
                });

                if (result.error) {
                    throw new Error(result.error.message);
                }
            } catch (error) {
                console.error('Error:', error);
                // Show error to customer
                const errorDiv = document.createElement('div');
                errorDiv.classList.add('alert', 'alert-danger', 'mt-3');
                errorDiv.textContent = error.message;
                button.parentElement.appendChild(errorDiv);

                // Reset button state
                button.disabled = false;
                button.textContent = 'Upgrade to Pro';

                // Remove error message after 5 seconds
                setTimeout(() => errorDiv.remove(), 5000);
            }
        });
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeFileUpload();
    initializeStripe();
});