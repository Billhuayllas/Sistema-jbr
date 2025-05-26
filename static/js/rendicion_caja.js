document.addEventListener('DOMContentLoaded', function() {
    // --- Cache DOM Elements ---
    // Add/Edit Form
    const addMovementForm = document.getElementById('addMovementForm');
    const transactionIdField = document.getElementById('transactionId'); // Hidden input for editing
    const fechaMovimientoField = document.getElementById('fechaMovimiento');
    const cuentaField = document.getElementById('cuenta');
    const bancoContainer = document.getElementById('banco-container');
    const bancoField = document.getElementById('banco');
    const tipoMovimientoField = document.getElementById('tipo');
    const montoField = document.getElementById('monto');
    const descripcionField = document.getElementById('desc');
    const agregarBtn = document.getElementById('caja-btn-agregar');
    const cancelarBtn = document.getElementById('caja-btn-cancelar');
    
    // Movimientos Actuales Section
    const verCuentaFilter = document.getElementById('verCuenta');
    const verCuentaBancoContainer = document.getElementById('verCuentaBanco-container'); // Ensure this ID is in HTML
    const verCuentaBancoFilter = document.getElementById('verCuentaBanco');
    const movimientosTableBody = document.getElementById('movimientos-body');
    const saldoTotalElement = document.getElementById('saldo-total');

    // Reporte Diario Section
    const fechaReporteField = document.getElementById('caja-fechaReporte');
    const buscarReporteBtn = document.getElementById('caja-buscar-reporte');
    const descargarReporteBtn = document.getElementById('caja-descargar-reporte'); // Placeholder
    const reporteTableBody = document.getElementById('caja-reporte-body');
    const netoCajaElement = document.getElementById('caja-neto-caja');
    const netoBancarioElement = document.getElementById('caja-neto-bancario');
    const netoGlobalElement = document.getElementById('caja-neto-global');

    // Historial Completo Section
    const fechaHistorialField = document.getElementById('caja-fechaHistorial');
    const buscarHistorialBtn = document.getElementById('caja-buscar-historial');
    const descargarHistorialBtn = document.getElementById('caja-descargar-historial'); // Placeholder
    const historialTableBody = document.getElementById('caja-historial-body');

    // Acciones Generales Buttons (Placeholders)
    const exportJsonBtn = document.getElementById('caja-exportar-json');
    const exportCsvBtn = document.getElementById('caja-exportar-csv');
    const importJsonBtn = document.getElementById('caja-importar-json');
    const realizarCorteBtn = document.getElementById('caja-realizar-corte');
    const limpiarDatosBtn = document.getElementById('caja-limpiar-datos');

    let editingTransactionId = null; // To keep track of which transaction is being edited

    // --- Helper Functions ---
    function formatCurrency(amount) {
        return `$${parseFloat(amount || 0).toFixed(2)}`;
    }

    function formatDateForInput(isoDateString) {
        if (!isoDateString) return '';
        // Assuming ISO format (YYYY-MM-DD) from server, which is fine for date input
        return isoDateString.split('T')[0]; 
    }

    // --- Conditional Display of "Banco" Dropdown ---
    function toggleBancoVisibility(cuentaElement, bancoContainerElement, bancoElementToSetRequired) {
        if (cuentaElement.value === 'CuentaBancaria') {
            bancoContainerElement.style.display = 'block';
            if (bancoElementToSetRequired) bancoElementToSetRequired.required = true;
        } else {
            bancoContainerElement.style.display = 'none';
            if (bancoElementToSetRequired) {
                bancoElementToSetRequired.required = false;
                bancoElementToSetRequired.value = ''; // Clear value if hidden
            }
        }
    }

    if (cuentaField && bancoContainer && bancoField) {
        cuentaField.addEventListener('change', () => toggleBancoVisibility(cuentaField, bancoContainer, bancoField));
        toggleBancoVisibility(cuentaField, bancoContainer, bancoField); // Initial check
    }

    if (verCuentaFilter && verCuentaBancoContainer && verCuentaBancoFilter) {
        verCuentaFilter.addEventListener('change', () => toggleBancoVisibility(verCuentaFilter, verCuentaBancoContainer, null)); // verCuentaBancoFilter is not required for filtering
        toggleBancoVisibility(verCuentaFilter, verCuentaBancoContainer, null); // Initial check
    }
    
    // --- Add/Edit Form Handling (AJAX) ---
    if (addMovementForm) {
        addMovementForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const formData = new FormData(addMovementForm);
            // const data = Object.fromEntries(formData.entries()); // Not strictly needed if sending FormData
            
            let url = editingTransactionId 
                ? `/cash_and_banks/edit_transaction/${editingTransactionId}` 
                : '/cash_and_banks/add_movement'; // URL for adding
            
            // Ensure 'banco' field in FormData is handled correctly if 'cuenta' is not 'CuentaBancaria'
            if (formData.get('cuenta') !== 'CuentaBancaria') {
                formData.set('banco', ''); // Set to empty string; server model can interpret as None
            }
            
            fetch(url, {
                method: 'POST',
                body: formData // FormData is suitable for Flask's request.form
            })
            .then(response => {
                // Assuming both add and edit routes now return JSON.
                // The backend subtask for routes should have ensured this.
                return response.json().then(jsonResponse => ({ 
                    ok: response.ok, 
                    status: response.status, 
                    body: jsonResponse 
                }));
            })
            .then(({ok, status, body}) => {
                if (ok && body.success) {
                    Swal.fire('¡Éxito!', body.message, 'success').then(() => {
                        window.location.reload(); // Reload to see changes
                    });
                    resetAddEditForm();
                } else {
                    Swal.fire('Error', body.message || `Error ${status}`, 'error');
                }
            })
            .catch(error => {
                console.error('Error submitting movement form:', error);
                Swal.fire('Error', 'Error de conexión o del servidor.', 'error');
            });
        });
    }

    function resetAddEditForm() {
        addMovementForm.reset();
        editingTransactionId = null;
        transactionIdField.value = ''; // Clear hidden ID field if it's used (not currently in form)
        if (agregarBtn) agregarBtn.innerHTML = '<i class="fas fa-plus"></i> Agregar Movimiento';
        if (agregarBtn) agregarBtn.classList.replace('btn-warning', 'btn-primary'); // If it was changed to warning for edit
        if (cancelarBtn) cancelarBtn.style.display = 'none';
        if (cuentaField) toggleBancoVisibility(cuentaField, bancoContainer, bancoField); // Reset banco visibility
        // Set default date if needed
        if(fechaMovimientoField && typeof initialTodayDate !== 'undefined') { // initialTodayDate passed from template
            fechaMovimientoField.value = initialTodayDate;
        }
    }
    
    if (cancelarBtn) {
        cancelarBtn.addEventListener('click', resetAddEditForm);
    }

    // --- Movimientos Actuales Table Interactions ---
    // Filter Changes (Reload page with query params)
    if (verCuentaFilter) {
        verCuentaFilter.addEventListener('change', applyMovimientosFilters);
    }
    if (verCuentaBancoFilter) {
        verCuentaBancoFilter.addEventListener('change', applyMovimientosFilters);
    }

    function applyMovimientosFilters() {
        const params = new URLSearchParams(window.location.search);
        if (verCuentaFilter.value) {
            params.set('ver_cuenta_filter', verCuentaFilter.value);
            if (verCuentaFilter.value === 'CuentaBancaria' && verCuentaBancoFilter.value) {
                params.set('ver_cuenta_banco_filter', verCuentaBancoFilter.value);
            } else {
                params.delete('ver_cuenta_banco_filter'); // Remove if not 'CuentaBancaria' or no specific bank
            }
        } else {
            params.delete('ver_cuenta_filter');
            params.delete('ver_cuenta_banco_filter');
        }
        window.location.search = params.toString();
    }

    // Edit Button
    if (movimientosTableBody) {
        movimientosTableBody.addEventListener('click', function(event) {
            const editButton = event.target.closest('.btnEditarMovimiento');
            if (editButton) {
                const id = editButton.dataset.id;
                fetch(`/cash_and_banks/transaction_details/${id}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            Swal.fire('Error', data.error, 'error'); return;
                        }
                        fechaMovimientoField.value = formatDateForInput(data.date);
                        cuentaField.value = data.cuenta;
                        toggleBancoVisibility(cuentaField, bancoContainer, bancoField); // Update banco visibility
                        if (data.cuenta === 'CuentaBancaria') {
                            bancoField.value = data.banco || '';
                        }
                        tipoMovimientoField.value = data.tipo_movimiento;
                        montoField.value = parseFloat(data.amount).toFixed(2);
                        descripcionField.value = data.descripcion;
                        
                        editingTransactionId = id;
                        // transactionIdField.value = id; // If using a hidden field
                        
                        if (agregarBtn) agregarBtn.innerHTML = '<i class="fas fa-save"></i> Actualizar Movimiento';
                        if (agregarBtn) agregarBtn.classList.replace('btn-primary','btn-warning');
                        if (cancelarBtn) cancelarBtn.style.display = 'inline-block';
                        
                        addMovementForm.scrollIntoView({ behavior: 'smooth' });
                    })
                    .catch(err => Swal.fire('Error', 'No se pudieron cargar los detalles.', 'error'));
            }

            // Delete Button
            const deleteButton = event.target.closest('.btnEliminarMovimiento');
            if (deleteButton) {
                const id = deleteButton.dataset.id;
                Swal.fire({
                    title: '¿Eliminar Movimiento?',
                    text: "Esta acción es permanente.",
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonColor: '#d33',
                    confirmButtonText: 'Sí, Eliminar',
                    cancelButtonText: 'Cancelar'
                }).then(result => {
                    if (result.isConfirmed) {
                        fetch(`/cash_and_banks/delete_transaction/${id}`, { method: 'POST' })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                Swal.fire('¡Eliminado!', data.message, 'success').then(() => window.location.reload());
                            } else {
                                Swal.fire('Error', data.message, 'error');
                            }
                        })
                        .catch(err => Swal.fire('Error', 'Error de conexión.', 'error'));
                    }
                });
            }
        });
    }

    // --- Reporte Diario Section ---
    if (buscarReporteBtn) {
        buscarReporteBtn.addEventListener('click', function() {
            const selectedDate = fechaReporteField.value;
            if (!selectedDate) {
                Swal.fire('Atención', 'Por favor, seleccione una fecha para el reporte.', 'warning');
                return;
            }
            fetch(`/cash_and_banks/reporte_diario_data?date=${selectedDate}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        Swal.fire('Error', data.error, 'error'); return;
                    }
                    renderReportTable(data.transactions);
                    if(netoCajaElement) netoCajaElement.textContent = formatCurrency(data.neto_caja);
                    if(netoBancarioElement) netoBancarioElement.textContent = formatCurrency(data.neto_bancario);
                    if(netoGlobalElement) netoGlobalElement.textContent = formatCurrency(data.neto_global);
                })
                .catch(err => Swal.fire('Error', 'No se pudo cargar el reporte.', 'error'));
        });
    }
    
    function renderReportTable(transactions) {
        if (!reporteTableBody) return;
        reporteTableBody.innerHTML = ''; // Clear existing rows
        if (transactions && transactions.length > 0) {
            transactions.forEach(tx => {
                const row = reporteTableBody.insertRow();
                row.insertCell().textContent = tx.date;
                row.insertCell().textContent = tx.descripcion;
                const tipoCell = row.insertCell();
                tipoCell.innerHTML = `<span class="badge bg-${tx.tipo_movimiento === 'Ingreso' ? 'success' : 'danger'}">${tx.tipo_movimiento}</span>`;
                const montoCell = row.insertCell();
                montoCell.textContent = formatCurrency(tx.amount);
                montoCell.classList.add('text-end');
                row.insertCell().textContent = tx.cuenta;
                row.insertCell().textContent = tx.cuenta === 'CuentaBancaria' ? (tx.banco || 'N/A') : 'N/A';
            });
        } else {
            const row = reporteTableBody.insertRow();
            const cell = row.insertCell();
            cell.colSpan = 6; // Number of columns in report table
            cell.textContent = 'No hay transacciones para la fecha seleccionada.';
            cell.classList.add('text-center', 'fst-italic', 'text-muted');
        }
    }
    // Initial render of report table if data is passed from Flask (e.g. report_transactions_today)
    // This requires report_transactions_today to be available globally or passed via data attribute.
    // Assuming Flask already renders the initial state of this table.

    // --- Historial Completo Section ---
    if (buscarHistorialBtn) {
        buscarHistorialBtn.addEventListener('click', function() {
            const selectedDate = fechaHistorialField.value; // Can be empty for all history
            let url = '/cash_and_banks/historial_data';
            if (selectedDate) {
                url += `?date=${selectedDate}`;
            }
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        Swal.fire('Error', data.error, 'error'); return;
                    }
                    renderHistorialTable(data.transactions);
                })
                .catch(err => Swal.fire('Error', 'No se pudo cargar el historial.', 'error'));
        });
    }

    function renderHistorialTable(transactions) {
        if (!historialTableBody) return;
        historialTableBody.innerHTML = ''; // Clear existing rows
        if (transactions && transactions.length > 0) {
            transactions.forEach(tx => {
                const row = historialTableBody.insertRow();
                row.insertCell().textContent = tx.date;
                row.insertCell().textContent = tx.descripcion;
                const tipoCell = row.insertCell();
                tipoCell.innerHTML = `<span class="badge bg-${tx.tipo_movimiento === 'Ingreso' ? 'success' : 'danger'}">${tx.tipo_movimiento}</span>`;
                const montoCell = row.insertCell();
                montoCell.textContent = formatCurrency(tx.amount);
                montoCell.classList.add('text-end');
                row.insertCell().textContent = tx.cuenta;
                row.insertCell().textContent = tx.cuenta === 'CuentaBancaria' ? (tx.banco || 'N/A') : 'N/A';
            });
        } else {
            const row = historialTableBody.insertRow();
            const cell = row.insertCell();
            cell.colSpan = 6; // Number of columns in historial table
            cell.textContent = 'No hay transacciones en el historial para la fecha seleccionada (o en total si no se especificó fecha).';
            cell.classList.add('text-center', 'fst-italic', 'text-muted');
        }
    }
    // Initial render of historial table is handled by Flask/Jinja for all_transactions_for_historial.

    // --- Placeholder Buttons ---
    const placeholderActions = [
        { id: 'caja-exportar-json', msg: 'Exportar Todo (JSON)'},
        { id: 'caja-exportar-csv', msg: 'Exportar Todo (CSV)'},
        { id: 'caja-importar-json', msg: 'Importar (JSON)'},
        { id: 'caja-realizar-corte', msg: 'Realizar Corte de Caja'},
        { id: 'caja-limpiar-datos', msg: 'Limpiar Datos Caja'},
        { id: 'caja-descargar-reporte', msg: 'Descargar Reporte (PNG)'},
        { id: 'caja-descargar-historial', msg: 'Descargar Historial (PNG)'}
    ];
    placeholderActions.forEach(action => {
        const btn = document.getElementById(action.id);
        if (btn) {
            btn.addEventListener('click', () => {
                // For 'caja-realizar-corte', we actually make a POST request
                if (action.id === 'caja-realizar-corte') {
                    Swal.fire({
                        title: '¿Realizar Corte de Caja?',
                        text: "Esta acción es compleja y podría modificar sus datos actuales. ¿Continuar?",
                        icon: 'warning',
                        showCancelButton: true,
                        confirmButtonText: 'Sí, proceder',
                        cancelButtonText: 'Cancelar'
                    }).then((result) => {
                        if (result.isConfirmed) {
                            fetch('/cash_and_banks/corte_de_caja', { method: 'POST' })
                                .then(response => response.json())
                                .then(data => {
                                    if (data.success) {
                                        Swal.fire('Corte de Caja', data.message, 'success');
                                    } else {
                                        Swal.fire('Corte de Caja', data.message || 'Funcionalidad no implementada.', 'info');
                                    }
                                })
                                .catch(err => Swal.fire('Error', 'Error de conexión.', 'error'));
                        }
                    });
                } else {
                    Swal.fire('Función en Desarrollo', `${action.msg}: Esta funcionalidad no está implementada todavía.`, 'info');
                }
            });
        }
    });

}); // End DOMContentLoaded
```
