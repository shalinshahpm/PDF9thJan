// Initialize the dropzone functionality
class PDFOperations {
    constructor() {
        this.dropZone = document.getElementById('drop-zone');
        this.fileInput = document.getElementById('file-input');
        this.fileList = document.getElementById('file-list');
        this.progressBar = document.querySelector('.progress-bar');
        this.files = [];

        this.initializeDropZone();
        this.initializeSortable();
    }

    initializeDropZone() {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, () => {
                this.dropZone.classList.add('border-primary');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, () => {
                this.dropZone.classList.remove('border-primary');
            });
        });

        this.dropZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            this.handleFiles(files);
        });

        this.dropZone.addEventListener('click', () => {
            this.fileInput.click();
        });

        this.fileInput.addEventListener('change', (e) => {
            this.handleFiles(e.target.files);
        });
    }

    initializeSortable() {
        if (this.fileList) {
            new Sortable(this.fileList, {
                animation: 150,
                ghostClass: 'bg-light'
            });
        }
    }

    handleFiles(fileList) {
        const newFiles = Array.from(fileList).filter(file => {
            if (!file.type.includes('pdf')) {
                this.showError('Only PDF files are allowed');
                return false;
            }
            return true;
        });

        this.files = [...this.files, ...newFiles];
        this.updateFileList();
    }

    updateFileList() {
        if (!this.fileList) return;

        this.fileList.innerHTML = '';
        this.files.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item d-flex align-items-center p-2 border-bottom';
            fileItem.innerHTML = `
                <i data-feather="file" class="me-2"></i>
                <span class="flex-grow-1">${file.name}</span>
                <button class="btn btn-sm btn-outline-danger" onclick="pdfOperations.removeFile(${index})">
                    <i data-feather="x"></i>
                </button>
            `;
            this.fileList.appendChild(fileItem);
        });
        feather.replace();
    }

    removeFile(index) {
        this.files.splice(index, 1);
        this.updateFileList();
    }

    updateProgress(percent) {
        if (this.progressBar) {
            this.progressBar.style.width = `${percent}%`;
            this.progressBar.setAttribute('aria-valuenow', percent);
            this.progressBar.parentElement.classList.toggle('d-none', percent === 0 || percent === 100);
        }
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.classList.add('alert', 'alert-danger', 'mt-3');
        errorDiv.textContent = message;
        this.dropZone.parentElement.appendChild(errorDiv);
        setTimeout(() => errorDiv.remove(), 5000);
    }

    async downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    async processOperation(operation) {
        if (this.files.length === 0) {
            this.showError('Please select at least one PDF file');
            return;
        }

        const formData = new FormData();
        this.updateProgress(0);

        try {
            // Add operation-specific parameters
            switch (operation) {
                case 'split':
                    const pageRanges = document.getElementById('page-ranges').value;
                    if (!pageRanges) {
                        this.showError('Please enter page ranges');
                        return;
                    }
                    formData.append('ranges', pageRanges);
                    formData.append('file', this.files[0]);
                    break;

                case 'merge':
                    this.files.forEach(file => formData.append('files[]', file));
                    break;

                case 'watermark':
                    const watermarkText = document.getElementById('watermark-text').value;
                    const position = document.getElementById('watermark-position').value;
                    const color = document.getElementById('watermark-color').value;
                    if (!watermarkText) {
                        this.showError('Please enter watermark text');
                        return;
                    }
                    formData.append('text', watermarkText);
                    formData.append('position', position);
                    formData.append('color', color);
                    formData.append('file', this.files[0]);
                    break;

                case 'toImages':
                    const format = document.getElementById('image-format').value;
                    const dpi = document.getElementById('image-dpi').value;
                    formData.append('format', format);
                    formData.append('dpi', dpi);
                    formData.append('file', this.files[0]);
                    break;

                case 'rotate':
                    const angle = document.getElementById('rotation-angle').value;
                    const pages = document.getElementById('rotation-pages').value;
                    formData.append('angle', angle);
                    formData.append('pages', pages);
                    formData.append('file', this.files[0]);
                    break;

                case 'addText':
                    const text = document.getElementById('add-text').value;
                    const x = document.getElementById('text-x').value;
                    const y = document.getElementById('text-y').value;
                    const textColor = document.getElementById('text-color').value;

                    if (!text) {
                        this.showError('Please enter text to add');
                        return;
                    }

                    formData.append('text', text);
                    formData.append('x', x);
                    formData.append('y', y);
                    formData.append('color', textColor);
                    formData.append('file', this.files[0]);
                    break;

                case 'extractText':
                    const extractPages = document.getElementById('extract-pages').value;
                    const extractFormat = document.getElementById('extract-format').value;
                    formData.append('pages', extractPages);
                    formData.append('format', extractFormat);
                    formData.append('file', this.files[0]);
                    break;

                case 'organize':
                    const layout = document.getElementById('page-layout').value;
                    formData.append('layout', layout);
                    formData.append('file', this.files[0]);
                    break;

                case 'secure':
                    const ownerPassword = document.getElementById('owner-password').value;
                    const userPassword = document.getElementById('user-password').value;
                    const allowPrint = document.getElementById('allow-print').checked;
                    const allowCopy = document.getElementById('allow-copy').checked;

                    if (!ownerPassword && !userPassword) {
                        this.showError('Please enter at least one password');
                        return;
                    }

                    formData.append('owner_password', ownerPassword);
                    formData.append('user_password', userPassword);
                    formData.append('allow_print', allowPrint);
                    formData.append('allow_copy', allowCopy);
                    formData.append('file', this.files[0]);
                    break;
            }

            this.updateProgress(20);
            const response = await fetch(`/pdf/${operation}`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Operation failed');
            }

            this.updateProgress(80);

            const contentType = response.headers.get('content-type');
            let blob;
            let filename;

            if (contentType.includes('json')) {
                const jsonData = await response.json();
                const jsonString = JSON.stringify(jsonData, null, 2);
                blob = new Blob([jsonString], { type: 'application/json' });
                filename = 'extracted_text.json';
            } else {
                blob = await response.blob();
                filename = response.headers.get('content-disposition')?.split('filename=')[1]?.replace(/"/g, '') || 'output';

                if (!filename.includes('.')) {
                    if (contentType.includes('pdf')) {
                        filename += '.pdf';
                    } else if (contentType.includes('zip')) {
                        filename += '.zip';
                    } else if (contentType.includes('text')) {
                        filename += '.txt';
                    }
                }
            }

            this.updateProgress(90);
            await this.downloadBlob(blob, filename);
            this.updateProgress(100);

            // Clean up
            this.files = [];
            this.updateFileList();

        } catch (error) {
            console.error('Operation error:', error);
            this.showError(error.message || 'An error occurred during the operation');
            this.updateProgress(0);
        }
    }
}

// Initialize the PDF operations handler
const pdfOperations = new PDFOperations();

// Global handler for operation buttons
function handleOperation(operation) {
    pdfOperations.processOperation(operation);
}