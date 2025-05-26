document.addEventListener('DOMContentLoaded', function () {
    const modalElement = document.getElementById('terceroModal');
    // Check if Bootstrap 5's Modal class is available
    const bootstrapModal = modalElement ? new bootstrap.Modal(modalElement) : null;
    
    const form = document.getElementById('terceroForm');
    const modalLabel = document.getElementById('terceroModalLabel');
    const btnAgregarTercero = document.getElementById('btnAgregarTercero');
    let editingTerceroId = null;

    // Custom modal show/hide if Bootstrap JS is not used for this specific modal
    // These are fallback if bootstrapModal is not available or not working as expected
    function showCustomModal() {
        if (modalElement) modalElement.style.display = 'block'; // Or 'flex' if styled that way
        document.body.classList.add('modal-open'); // Optional: prevent body scroll
    }

    function hideCustomModal() {
        if (modalElement) modalElement.style.display = 'none';
        document.body.classList.remove('modal-open');
    }

    function openModal(title, id = null) {
        if (!form) return;
        form.reset();
        form.classList.remove('was-validated'); // For Bootstrap validation styles
        if(modalLabel) modalLabel.textContent = title;
        editingTerceroId = id;
        const idField = document.getElementById('terceroId');
        if(idField) idField.value = id || '';

        if (id) { // Editing mode
            fetch(`/terceros/details/${id}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success === false || data.error) { // Check for explicit error from backend
                        Swal.fire('Error', data.message || data.error || 'No se pudieron cargar los datos del tercero.', 'error');
                        return;
                    }
                    document.getElementById('terceroNombre').value = data.nombre || '';
                    document.getElementById('terceroDNI').value = data.dni || '';
                    document.getElementById('terceroDireccionPrincipal').value = data.direccion_principal || '';
                    document.getElementById('terceroEnvioDepartamento').value = data.envio_departamento || '';
                    document.getElementById('terceroEnvioAgencia').value = data.envio_agencia || '';
                    document.getElementById('terceroEnvioNotas').value = data.envio_notas || '';
                    document.getElementById('terceroTelefono').value = data.telefono || '';
                    document.getElementById('terceroEmail').value = data.email || '';
                })
                .catch(error => Swal.fire('Error', 'Error de red al cargar datos del tercero.', 'error'));
        }
        
        if (bootstrapModal) bootstrapModal.show();
        else showCustomModal();
    }

    function closeModal() {
        if (bootstrapModal) bootstrapModal.hide();
        else hideCustomModal();
    }
    
    // Setup close buttons for modal (both custom and Bootstrap ones)
    modalElement?.querySelectorAll('.close-btn, [data-bs-dismiss="modal"]').forEach(btn => {
        btn.addEventListener('click', () => closeModal());
    });
    // Close on backdrop click for custom modal (Bootstrap handles this natively)
    if (!bootstrapModal && modalElement) {
        modalElement.addEventListener('click', (event) => { 
            if (event.target === modalElement) closeModal();
        });
    }

    if (btnAgregarTercero) {
        btnAgregarTercero.addEventListener('click', () => {
            openModal('Agregar Nuevo Tercero');
        });
    }

    document.getElementById('tercerosTableBody')?.addEventListener('click', function (event) {
        const editButton = event.target.closest('.btnEditarTercero');
        const deleteButton = event.target.closest('.btnEliminarTercero');

        if (editButton) {
            const id = editButton.dataset.id;
            openModal('Editar Tercero', id);
        } else if (deleteButton) {
            const id = deleteButton.dataset.id;
            const nombre = deleteButton.closest('tr')?.querySelector('td')?.textContent || 'este tercero'; 
            Swal.fire({
                title: `¿Eliminar a ${nombre}?`,
                text: "Esta acción no se puede deshacer.",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#6c757d', // BS secondary color
                confirmButtonText: 'Sí, eliminar',
                cancelButtonText: 'Cancelar'
            }).then((result) => {
                if (result.isConfirmed) {
                    fetch(`/terceros/delete/${id}`, { method: 'POST' }) 
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                Swal.fire('Eliminado', data.message, 'success').then(() => window.location.reload());
                            } else {
                                Swal.fire('Error', data.message || 'No se pudo eliminar el tercero.', 'error');
                            }
                        })
                        .catch(error => Swal.fire('Error', 'Error de red al eliminar.', 'error'));
                }
            });
        }
    });

    if (form) {
        form.addEventListener('submit', function (event) {
            event.preventDefault();
            // HTML5 validation check
            if (!form.checkValidity()) {
                form.classList.add('was-validated'); // Trigger Bootstrap validation styles
                // Optionally, show a generic message or rely on browser's default for invalid fields
                // Swal.fire('Datos Inválidos', 'Por favor, corrija los errores en el formulario.', 'warning');
                return;
            }
            form.classList.remove('was-validated');


            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());
            const url = editingTerceroId ? `/terceros/edit/${editingTerceroId}` : '/terceros/add';

            fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    closeModal();
                    Swal.fire('Guardado', result.message, 'success').then(() => window.location.reload());
                } else {
                    Swal.fire('Error', result.message || 'No se pudo guardar el tercero.', 'error');
                }
            })
            .catch(error => Swal.fire('Error', 'Error de red al guardar.', 'error'));
        });
    }
});
```
