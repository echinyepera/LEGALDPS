document.addEventListener('DOMContentLoaded', () => {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const fileList = document.getElementById('fileList');
    const processBtn = document.getElementById('processBtn');
    const resultsList = document.getElementById('resultsList');
    const emptyState = document.getElementById('emptyState');
    const systemLogs = document.getElementById('systemLogs');
    const statusBadge = document.getElementById('statusBadge');
    const progressBarContainer = document.getElementById('progressBarContainer');
    const progressBar = document.getElementById('progressBar');
    const progressStatus = document.getElementById('progressStatus');
    const termsInput = document.getElementById('termsInput');
    const redactionConfig = document.getElementById('redactionConfig');
    const operationRadios = document.getElementsByName('operation');

    const progressPercentage = document.getElementById('progressPercentage');
    const operationHint = document.getElementById('operationHint');

    let uploadedFiles = [];

    // Drag and Drop
    dropzone.addEventListener('click', () => fileInput.click());
    
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });

    fileInput.addEventListener('change', () => {
        handleFiles(fileInput.files);
    });

    // Handle Operation Selection
    operationRadios.forEach(radio => {
        radio.addEventListener('change', () => {
            if (radio.value === 'redact') {
                redactionConfig.classList.remove('hidden');
                operationHint.classList.add('hidden');
            } else {
                redactionConfig.classList.add('hidden');
                operationHint.classList.remove('hidden');
            }
        });
    });

    function addLog(message, type = 'INFO') {
        const p = document.createElement('p');
        p.className = 'log-entry animate-slide-up';
        const typeClass = type === 'ERROR' ? 'log-error' : 
                          type === 'SUCCESS' ? 'log-success' : 'log-info';
        
        p.innerHTML = `<span class="${typeClass}">[${type}]</span> <span class="text-slate-500">${new Date().toLocaleTimeString()}</span> ${message}`;
        systemLogs.appendChild(p);
        systemLogs.scrollTop = systemLogs.scrollHeight;
    }

    async function handleFiles(files) {
        if (files.length === 0) return;

        const formData = new FormData();
        for (const file of files) {
            formData.append('files', file);
        }

        addLog(`Initiating secure upload for ${files.length} document(s)...`);
        statusBadge.textContent = 'Uploading';
        statusBadge.className = 'badge badge-processing';

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (data.error) throw new Error(data.error);

            uploadedFiles = [...uploadedFiles, ...data.files];
            updateFileList();
            addLog(`Upload sequence complete. Integrity verified for: ${data.files.join(', ')}`, 'SUCCESS');
            
            statusBadge.textContent = 'Ready';
            statusBadge.className = 'badge badge-success';
        } catch (error) {
            addLog(`Protocol breach: ${error.message}`, 'ERROR');
            statusBadge.textContent = 'Error';
            statusBadge.className = 'badge bg-red-100 text-red-700';
        }
    }

    function updateFileList() {
        fileList.innerHTML = '';
        uploadedFiles.forEach((filename, index) => {
            const div = document.createElement('div');
            div.className = 'flex items-center justify-between p-4 bg-white rounded-xl border border-slate-100 shadow-sm animate-slide-up';
            div.innerHTML = `
                <div class="flex items-center overflow-hidden">
                    <div class="w-8 h-8 rounded bg-red-50 flex items-center justify-center mr-3">
                        <i class="fas fa-file-pdf text-red-500 text-xs"></i>
                    </div>
                    <div>
                        <p class="text-xs font-bold text-slate-800 truncate">${filename}</p>
                        <p class="text-[10px] text-slate-400 uppercase tracking-tighter">Ready for processing</p>
                    </div>
                </div>
                <button onclick="removeFile(${index})" class="w-8 h-8 rounded-full hover:bg-red-50 text-slate-300 hover:text-red-500 transition-colors">
                    <i class="fas fa-times text-xs"></i>
                </button>
            `;
            fileList.appendChild(div);
        });
        processBtn.disabled = uploadedFiles.length === 0;
    }

    window.removeFile = (index) => {
        const removed = uploadedFiles.splice(index, 1);
        addLog(`Document decommissioned: ${removed}`);
        updateFileList();
    };

    processBtn.addEventListener('click', async () => {
        const operation = document.querySelector('input[name="operation"]:checked').value;
        const terms = termsInput.value;

        if (uploadedFiles.length === 0) return;

        emptyState.classList.add('hidden');
        progressBarContainer.classList.remove('hidden');
        progressBar.style.width = '0%';
        progressPercentage.textContent = '0%';
        progressStatus.textContent = 'Initializing intelligence engines...';
        statusBadge.textContent = 'Executing';
        statusBadge.className = 'badge badge-processing';
        processBtn.disabled = true;

        addLog(`Protocol started: ${operation.toUpperCase()} sequence initiated...`);

        try {
            const response = await fetch('/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    operation: operation,
                    files: uploadedFiles,
                    terms: terms
                })
            });

            const { task_id, error } = await response.json();
            if (error) throw new Error(error);

            // Poll for status
            pollTaskStatus(task_id);

        } catch (error) {
            addLog(`Execution failure: ${error.message}`, 'ERROR');
            statusBadge.textContent = 'Failed';
            statusBadge.className = 'badge bg-red-100 text-red-700';
            progressBarContainer.classList.add('hidden');
            processBtn.disabled = false;
        }
    });

    async function pollTaskStatus(taskId) {
        let progress = 0;
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`/task_status/${taskId}`);
                const data = await response.json();

                if (data.status === 'processing') {
                    // Update UI with simulated progress while waiting
                    if (progress < 95) {
                        progress += Math.random() * 5;
                        const rounded = Math.round(progress);
                        progressBar.style.width = `${rounded}%`;
                        progressPercentage.textContent = `${rounded}%`;
                        if (rounded > 30 && rounded < 60) progressStatus.textContent = 'Performing structural analysis...';
                        if (rounded > 60 && rounded < 90) progressStatus.textContent = 'Applying intelligent transformations...';
                    }
                } else if (data.status === 'completed') {
                    clearInterval(pollInterval);
                    progressBar.style.width = '100%';
                    progressPercentage.textContent = '100%';
                    addLog(`Sequence completed successfully. Output generated.`, 'SUCCESS');
                    displayResults(data.results);
                    statusBadge.textContent = 'Finished';
                    statusBadge.className = 'badge badge-success';
                    setTimeout(() => {
                        progressBarContainer.classList.add('hidden');
                        processBtn.disabled = false;
                    }, 1500);
                } else if (data.status === 'failed') {
                    clearInterval(pollInterval);
                    throw new Error(data.error);
                }
            } catch (error) {
                clearInterval(pollInterval);
                addLog(`Processing error: ${error.message}`, 'ERROR');
                statusBadge.textContent = 'Failed';
                statusBadge.className = 'badge bg-red-100 text-red-700';
                progressBarContainer.classList.add('hidden');
                processBtn.disabled = false;
            }
        }, 1000);
    }

    function displayResults(results) {
        results.forEach(result => {
            const div = document.createElement('div');
            div.className = 'result-item bg-white border border-slate-100 rounded-2xl p-5 flex items-center justify-between shadow-sm animate-slide-up';
            
            const icon = result.type === 'pdf' ? 'fa-file-pdf text-red-500' : 
                         result.type === 'csv' ? 'fa-file-excel text-emerald-600' : 'fa-file-alt text-blue-500';
            
            const bg = result.type === 'pdf' ? 'bg-red-50' : 
                       result.type === 'csv' ? 'bg-emerald-50' : 'bg-blue-50';

            div.innerHTML = `
                <div class="flex items-center overflow-hidden">
                    <div class="w-12 h-12 rounded-xl ${bg} flex items-center justify-center mr-4 shadow-inner">
                        <i class="fas ${icon} text-xl"></i>
                    </div>
                    <div>
                        <p class="text-sm font-bold text-slate-800 truncate max-w-[180px]">${result.processed}</p>
                        <p class="text-[10px] text-slate-400 font-medium">Source: ${result.original}</p>
                    </div>
                </div>
                <a href="/download/${result.processed}" class="flex items-center px-6 py-2.5 bg-primary text-accent rounded-full text-xs font-bold hover:bg-slate-800 transition-all shadow-lg shadow-primary/10">
                    <i class="fas fa-download mr-2"></i> DOWNLOAD
                </a>
            `;
            resultsList.prepend(div);
        });
    }
});
