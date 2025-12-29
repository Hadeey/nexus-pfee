const getApibox = () => ({
    url: document.getElementById('api-url').value.replace(/\/$/, ''),
    token: document.getElementById('api-token').value
});

const showStatus = (elementId, message, type) => {
    const el = document.getElementById(elementId);
    el.innerText = message;
    el.className = `status-msg ${type}`;
    setTimeout(() => { el.innerText = ''; el.className = 'status-msg'; }, 5000);
};

// 1. UPLOAD
async function uploadFile() {
    const { url, token } = getApibox();
    const patientId = document.getElementById('upload-patient-id').value;
    const fileInput = document.getElementById('file-upload');

    if (!fileInput.files[0]) return showStatus('upload-status', 'Veuillez sélectionner un fichier', 'error');

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        const res = await fetch(`${url}/upload/${patientId}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });
        const data = await res.json();

        if (res.ok) {
            showStatus('upload-status', `Succès ! Stocké : ${data.file}`, 'success');
            fetchLogs();
            // Préfemplir la lecture
            document.getElementById('read-patient-id').value = patientId;
            document.getElementById('read-filename').value = data.file;
        } else {
            showStatus('upload-status', `Erreur: ${data.detail || res.statusText}`, 'error');
        }
    } catch (e) {
        showStatus('upload-status', `Erreur réseau: ${e}`, 'error');
    }
}

// 2. REVOKE
async function revokeAccess() {
    const { url, token } = getApibox();
    const patientId = document.getElementById('revoke-patient-id').value;

    try {
        const res = await fetch(`${url}/revoke/${patientId}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();

        if (res.ok) {
            showStatus('revoke-status', 'Consentement Révoqué ! Accès futurs bloqués.', 'success');
            fetchLogs();
        } else {
            showStatus('revoke-status', `Erreur: ${data.detail}`, 'error');
        }
    } catch (e) {
        showStatus('revoke-status', `Erreur réseau: ${e}`, 'error');
    }
}

// 3. READ
async function readFile() {
    const { url, token } = getApibox();
    const patientId = document.getElementById('read-patient-id').value;
    const filename = document.getElementById('read-filename').value;
    const display = document.getElementById('file-content-display');

    try {
        const res = await fetch(`${url}/read/${patientId}/${filename}`, {
            method: 'GET',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.ok) {
            const text = await res.text(); // Ou blob() pour images
            display.style.display = 'block';
            display.innerText = text;
            showStatus('read-status', 'Fichier déchiffré avec succès', 'success');
        } else {
            const data = await res.json();
            display.style.display = 'none';
            showStatus('read-status', `ACCÈS REFUSÉ : ${data.detail}`, 'error');
        }
        fetchLogs();
    } catch (e) {
        showStatus('read-status', `Erreur réseau: ${e}`, 'error');
    }
}

// 4. LOGS
async function fetchLogs() {
    const { url, token } = getApibox();
    const tbody = document.getElementById('logs-table-body');

    try {
        const res = await fetch(`${url}/logs`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            const logs = await res.json();
            tbody.innerHTML = logs.map(log => `
                <tr>
                    <td>${new Date(log.timestamp).toLocaleTimeString()}</td>
                    <td>${log.patient_id}</td>
                    <td>${log.action}</td>
                    <td>${log.requester}</td>
                    <td class="status-${log.status}">${log.status}</td>
                    <td>${log.details}</td>
                </tr>
            `).join('');
        }
    } catch (e) {
        console.error("Impossible de charger les logs", e);
    }
}

// Init
setInterval(fetchLogs, 5000); // Auto-refresh
fetchLogs();
