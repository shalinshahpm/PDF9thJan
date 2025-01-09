class PDFDropzone {
    constructor(options = {}) {
        this.dropzoneElement = options.element || document.getElementById('drop-zone');
        this.fileInput = options.fileInput || document.getElementById('file-input');
        this.maxFileSize = options.maxFileSize || 16 * 1024 * 1024; // 16MB
        this.acceptedFiles = options.acceptedFiles || ['.pdf'];
        this.currentFiles = [];
        this.progressBar = document.querySelector('.progress-bar');
        
        this.init();
    }

    init() {
        if (!this.dropzoneElement) return;

        this.bindEvents();
        this.initFileInput();
    }

    bindEvents() {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(event => {
            this.dropzoneElement.addEventListener(event, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        ['dragenter', 'dragover'].forEach(event => {
            this.dropzoneElement.addEventListener(event, () => {
                this.dropzoneElement.classList.add('highlight');
            });
        });

        ['dragleave', 'drop'].forEach(event => {
            this.dropzoneElement.addEventListener(event, () => {
                this.dropzoneElement.classList.remove('highlight');
            });
        });

        this.dropzoneElement.addEventListener('drop', (e) => {
            this.handleFiles(e.dataTransfer.files);
        });

        this.dropzoneElement.addEventListener('click', () => {
            this.fileInput.click();
        });
    }

    initFileInput() {
        this.fileInput.addEventListener('change', (e) => {
            this.handleFiles(e.target.files);
        });
    }

    handleFiles(files) {
        const validFiles = Array.from(files).filter(file => {
            const isValid = this.validateFile(file);
            if (!isValid) {
                this.showError(`File ${file.name} is not valid. Please check file type and size.`);
            }
            return isValid;
        });

        if (validFiles.length === 0) return;

        this.currentFiles = validFiles;
        this.showFileList();
        this.updateProgressBar(0);
    }

    validateFile(file) {
        if (file.size > this.maxFileSize) {
            return false;
        }

        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        return this.acceptedFiles.includes(fileExtension);
    }

    showFileList() {
        const fileListElement = document.createElement('div');
        fileListElement.className = 'file-list mt-3';

        this.currentFiles.forEach(file => {
            const fileElement = document.createElement('div');
            fileElement.className = 'file-item d-flex align-items-center mb-2';
            fileElement.innerHTML = `
                <i data-feather="file" class="me-2"></i>
                <span class="flex-grow-1">${file.name}</span>
                <button class="btn btn-sm btn-outline-danger" onclick="dropzone.removeFile('${file.name}')">
                    <i data-feather="x"></i>
                </button>
            `;
            fileListElement.appendChild(fileElement);
        });

        const existingFileList = this.dropzoneElement.querySelector('.file-list');
        if (existingFileList) {
            existingFileList.remove();
        }
        this.dropzoneElement.appendChild(fileListElement);
        feather.replace();
    }

    removeFile(fileName) {
        this.currentFiles = this.currentFiles.filter(file => file.name !== fileName);
        this.showFileList();
        if (this.currentFiles.length === 0) {
            this.resetDropzone();
        }
    }

    resetDropzone() {
        this.fileInput.value = '';
        this.currentFiles = [];
        const fileList = this.dropzoneElement.querySelector('.file-list');
        if (fileList) {
            fileList.remove();
        }
        this.updateProgressBar(0);
        this.progressBar.classList.add('d-none');
    }

    updateProgressBar(percentage) {
        if (this.progressBar) {
            this.progressBar.style.width = `${percentage}%`;
            this.progressBar.setAttribute('aria-valuenow', percentage);
            
            if (percentage > 0) {
                this.progressBar.classList.remove('d-none');
            }
        }
    }

    showError(message) {
        const alertElement = document.createElement('div');
        alertElement.className = 'alert alert-danger alert-dismissible fade show mt-3';
        alertElement.role = 'alert';
        alertElement.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        this.dropzoneElement.appendChild(alertElement);
        
        setTimeout(() => {
            alertElement.remove();
        }, 5000);
    }
}

// Initialize Dropzone
const dropzone = new PDFDropzone({
    maxFileSize: 16 * 1024 * 1024,
    acceptedFiles: ['.pdf']
});
