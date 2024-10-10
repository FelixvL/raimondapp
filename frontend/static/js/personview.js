document.addEventListener('DOMContentLoaded', function() {
    const presentieLogsModal = document.getElementById('presentieLogsModal');
    const presentieLogsTableBody = document.getElementById('presentieLogsTableBody');

    presentieLogsModal.addEventListener('show.bs.modal', function (event) {
        const personId = 1;
        
        // API-aanroep om presentiegegevens op te halen
        fetch(`/api/presentie_logs/${personId}`)
            .then(response => response.json())
            .then(data => {
                presentieLogsTableBody.innerHTML = '';
                
                // Vul de tabel met de opgehaalde gegevens, yippie type shit
                data.forEach(log => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${log.datum}</td>
                        <td>${log.tijd}</td>
                        <td>${log.status}</td>
                    `;
                    presentieLogsTableBody.appendChild(row);
                });
            })
            .catch(error => {
                console.error('Error:', error);
                presentieLogsTableBody.innerHTML = '<tr><td colspan="3">Er is een fout opgetreden bij het ophalen van de presentiegegevens.</td></tr>';
            });
    });
});