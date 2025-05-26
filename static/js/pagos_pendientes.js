document.addEventListener('DOMContentLoaded', function() {
    // --- Tab Switching Logic ---
    const tabs = document.querySelectorAll('.tabs-container .tabs .tab');
    const tabPanes = document.querySelectorAll('.tabs-container .tab-pane');

    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // Deactivate all tabs and panes
            tabs.forEach(t => t.classList.remove('active'));
            tabPanes.forEach(tp => {
                tp.classList.remove('active');
                tp.style.display = 'none'; // Ensure pane is hidden
            });

            // Activate clicked tab and corresponding pane
            this.classList.add('active');
            const targetPaneId = this.dataset.tabTarget;
            const targetPane = document.querySelector(targetPaneId);
            if (targetPane) {
                targetPane.classList.add('active');
                targetPane.style.display = 'block'; // Ensure pane is shown
            } else {
                console.error('Target tab pane not found:', targetPaneId);
            }
        });
    });

    // Initialize: Ensure only the active tab's content is displayed on page load
    // This might already be handled by initial HTML classes, but good for JS control
    let activeTabFound = false;
    tabs.forEach(tab => {
        if (tab.classList.contains('active')) {
            const targetPaneId = tab.dataset.tabTarget;
            const targetPane = document.querySelector(targetPaneId);
            if (targetPane) {
                targetPane.style.display = 'block';
                targetPane.classList.add('active'); // Ensure class consistency
                activeTabFound = true;
            }
        }
    });
    // If no tab was explicitly active, default to the first one
    if (!activeTabFound && tabs.length > 0) {
        tabs[0].click(); // Simulate a click to activate the first tab and its pane
    }


    // --- "Mark as Pagado" Functionality ---
    const pagosPendientesBody = document.getElementById('pagos-pendientes-body');
    if (pagosPendientesBody) {
        pagosPendientesBody.addEventListener('click', function(event) {
            const target = event.target.closest('.btn-pagado');
            if (target) {
                const entryId = target.dataset.id;
                Swal.fire({
                    title: 'Confirmar Pago',
                    text: "Marcar como Pagado? El registro se moverá al historial.",
                    icon: 'question',
                    showCancelButton: true,
                    confirmButtonColor: '#28a745', // Green for success
                    cancelButtonColor: '#6c757d',  // Grey for cancel
                    confirmButtonText: 'Sí, Marcar Pagado',
                    cancelButtonText: 'Cancelar'
                }).then((result) => {
                    if (result.isConfirmed) {
                        fetch(`/accounts_receivable/mark_paid/${entryId}`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json', // Though not strictly needed for this POST
                                // Add CSRF token header if/when implemented
                            }
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                Swal.fire('¡Pagado!', data.message || 'La entrada ha sido marcada como pagada.', 'success')
                                .then(() => window.location.reload());
                            } else {
                                Swal.fire('Error', data.message || 'No se pudo marcar como pagada.', 'error');
                            }
                        })
                        .catch(error => {
                            console.error('Error marking as paid:', error);
                            Swal.fire('Error', 'Error de conexión o del servidor.', 'error');
                        });
                    }
                });
            }
        });
    }


    // --- Client-Side Search for Tables ---
    function setupTableSearch(searchInputId, tableBodyId) {
        const searchInput = document.getElementById(searchInputId);
        const tableBody = document.getElementById(tableBodyId);

        if (searchInput && tableBody) {
            searchInput.addEventListener('input', function() {
                const searchTerm = this.value.toLowerCase().trim();
                const rows = tableBody.querySelectorAll('tr:not(.empty-row)'); // Exclude any existing empty row
                let visibleRows = 0;

                rows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    let rowText = '';
                    // Concatenate text from all cells except the actions cell
                    for (let i = 0; i < cells.length - (row.querySelector('.table-actions') ? 1 : 0); i++) {
                        rowText += cells[i].textContent.toLowerCase() + ' ';
                    }

                    if (rowText.includes(searchTerm)) {
                        row.style.display = '';
                        visibleRows++;
                    } else {
                        row.style.display = 'none';
                    }
                });

                // Handle empty state message
                let emptyRow = tableBody.querySelector('.empty-row');
                if (!emptyRow) { // Create one if it doesn't exist
                    emptyRow = document.createElement('tr');
                    emptyRow.classList.add('empty-row');
                    const cell = document.createElement('td');
                    cell.colSpan = tableBody.closest('table').querySelector('thead tr').children.length; // Span all columns
                    emptyRow.appendChild(cell);
                    // Prepend or append based on preference, append is simpler
                    tableBody.appendChild(emptyRow); 
                }

                if (visibleRows === 0) {
                    emptyRow.style.display = 'table-row';
                    emptyRow.querySelector('td').textContent = 'No hay resultados que coincidan con la búsqueda.';
                } else {
                    emptyRow.style.display = 'none';
                }
            });
        } else {
            // console.warn(`Search input ${searchInputId} or table body ${tableBodyId} not found.`);
        }
    }

    setupTableSearch('pagos-buscar', 'pagos-pendientes-body');
    setupTableSearch('pagos-buscar-historial', 'pagos-historial-body');


    // --- Edit/Delete Button Enhancements (Optional) ---
    // Delete confirmation (enhancing existing form submissions)
    document.querySelectorAll('form.delete-product-form, form.inline-form[action*="/delete/"]').forEach(form => {
        form.addEventListener('submit', function(event) {
            event.preventDefault(); // Stop direct submission
            Swal.fire({
                title: '¿Eliminar Registro?',
                text: "Esta acción es permanente. ¿Está seguro?",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#6c757d',
                confirmButtonText: 'Sí, Eliminar',
                cancelButtonText: 'Cancelar'
            }).then((result) => {
                if (result.isConfirmed) {
                    form.submit(); // Proceed with original form submission
                }
            });
        });
    });


    // --- Placeholder Buttons for Import/Export/Download ---
    const placeholderButtonIds = [
        'btnExportarPendientesJSON', 'btnExportarPendientesCSV', 
        'btnImportarPendientesJSON', 'btnDescargarTablaPendientesPDF',
        'btnExportarHistorialJSON', 'btnExportarHistorialCSV'
    ];

    placeholderButtonIds.forEach(id => {
        const button = document.getElementById(id);
        if (button) {
            button.addEventListener('click', function() {
                Swal.fire({
                    title: 'Función en Desarrollo',
                    text: 'Esta funcionalidad no está implementada todavía.',
                    icon: 'info',
                    confirmButtonText: 'Entendido'
                });
            });
        }
    });

}); // End DOMContentLoaded
```
