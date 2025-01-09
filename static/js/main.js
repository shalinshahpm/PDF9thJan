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
function initializeStripe() {
    const stripe = Stripe('your_publishable_key');
    const buttons = document.querySelectorAll('.subscribe-button');
    
    buttons.forEach(button => {
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            const priceId = button.getAttribute('data-price-id');
            
            try {
                const response = await fetch('/subscription/create-checkout-session', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `price_id=${priceId}`
                });
                
                const session = await response.json();
                const result = await stripe.redirectToCheckout({
                    sessionId: session.sessionId
                });
                
                if (result.error) {
                    alert(result.error.message);
                }
            } catch (error) {
                console.error('Error:', error);
            }
        });
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeFileUpload();
    initializeStripe();
});
