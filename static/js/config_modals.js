document.addEventListener('DOMContentLoaded', function () {
    // --- Generic Modal Handler ---
    function setupConfigModal(modalId, formId, addBtnId, editBtnClass, deleteBtnClass, fields, urls, entityName, populateFormCallback, getRowDataCallback) {
        const modalElement = document.getElementById(modalId);
        if (!modalElement) { 
            // console.warn(`Modal element ${modalId} not found. Skipping setup for ${entityName}.`);
            return; 
        }
        const modal = new bootstrap.Modal(modalElement);
        const form = document.getElementById(formId);
        const entityIdField = form.querySelector('input[type="hidden"]'); // Assumes first hidden input is ID, e.g., serieId, categoryId

        function resetForm() {
            form.reset();
            if (entityIdField) entityIdField.value = '';
            // Reset specific fields if needed, e.g., color input default
            if (fields.includes('color')) {
                const colorField = form.querySelector('[name="color"]');
                if (colorField) colorField.value = '#7f8c8d'; // Default color
            }
            const modalLabel = modalElement.querySelector('.modal-title');
            if (modalLabel) modalLabel.textContent = `Agregar ${entityName}`;
        }

        // Open modal for "Add"
        const addBtn = document.getElementById(addBtnId);
        if (addBtn) {
            addBtn.addEventListener('click', function () {
                resetForm();
                if (entityIdField) entityIdField.name = `${entityName.toLowerCase().replace(/\s+/g, '')}Id`; // e.g. serieId, categoryId, marcaId
                modal.show();
            });
        } else {
            // console.warn(`Add button ${addBtnId} not found for ${entityName}.`);
        }

        // Open modal for "Edit"
        document.querySelectorAll(`.${editBtnClass}`).forEach(button => {
            button.addEventListener('click', function () {
                const entityId = this.dataset.id;
                resetForm();
                if (entityIdField) {
                    entityIdField.value = entityId;
                    entityIdField.name = `${entityName.toLowerCase().replace(/\s+/g, '')}Id`;
                }
                const modalLabel = modalElement.querySelector('.modal-title');
                if (modalLabel) modalLabel.textContent = `Editar ${entityName}`;

                fetch(`${urls.detailsBase}/${entityId}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            Swal.fire('Error', data.error, 'error');
                            return;
                        }
                        if (populateFormCallback) {
                            populateFormCallback(form, data);
                        } else { // Default population
                            fields.forEach(field => {
                                const input = form.querySelector(`[name="${field}"]`);
                                if (input) input.value = data[field] !== undefined ? data[field] : '';
                            });
                        }
                        modal.show();
                    })
                    .catch(error => Swal.fire('Error', `No se pudieron cargar los detalles de ${entityName.toLowerCase()}.`, 'error'));
            });
        });

        // Form Submission (Add/Edit)
        if (form) {
            form.addEventListener('submit', function (event) {
                event.preventDefault();
                const entityId = entityIdField ? entityIdField.value : null;
                const url = entityId ? `${urls.editBase}/${entityId}` : urls.addBase;
                const formData = new FormData(form);
                const payload = Object.fromEntries(formData.entries());

                // Codigo field for Series should be disabled for edit, handle if not sent
                if (entityName === 'Serie' && entityId && !payload.codigo) {
                    const codigoInput = form.querySelector('[name="codigo"]');
                    if (codigoInput && codigoInput.disabled) {
                        payload.codigo = codigoInput.value; // Add it back if disabled
                    }
                }


                fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        modal.hide();
                        Swal.fire('¡Éxito!', data.message, 'success').then(() => window.location.reload());
                    } else {
                        Swal.fire('Error', data.message || `Ocurrió un error al guardar ${entityName.toLowerCase()}.`, 'error');
                    }
                })
                .catch(error => Swal.fire('Error', `Error de conexión o del servidor. ${error}`, 'error'));
            });
        } else {
            // console.warn(`Form ${formId} not found for ${entityName}.`);
        }

        // Delete
        document.querySelectorAll(`.${deleteBtnClass}`).forEach(button => {
            button.addEventListener('click', function () {
                const entityId = this.dataset.id;
                Swal.fire({
                    title: '¿Está seguro?',
                    text: `¡No podrá revertir esta acción de eliminar ${entityName.toLowerCase()}!`,
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonColor: '#d33',
                    cancelButtonColor: '#3085d6',
                    confirmButtonText: 'Sí, eliminar',
                    cancelButtonText: 'Cancelar'
                }).then((result) => {
                    if (result.isConfirmed) {
                        fetch(`${urls.deleteBase}/${entityId}`, { method: 'POST' })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                Swal.fire('¡Eliminado!', data.message, 'success').then(() => window.location.reload());
                            } else {
                                Swal.fire('Error', data.message || `No se pudo eliminar ${entityName.toLowerCase()}.`, 'error');
                            }
                        })
                        .catch(error => Swal.fire('Error', 'Error de conexión.', 'error'));
                    }
                });
            });
        });
    }

    // --- Setup for Series ---
    function populateSeriesForm(form, data) {
        form.querySelector('[name="codigo"]').value = data.codigo || '';
        form.querySelector('[name="nombre"]').value = data.nombre || '';
        form.querySelector('[name="color"]').value = data.color || '#7f8c8d';
        // Disable 'codigo' field when editing
        form.querySelector('[name="codigo"]').disabled = true; 
    }
    // When adding a new series, re-enable the codigo field
    const addSerieBtn = document.getElementById('btnAgregarSerie');
    if (addSerieBtn) {
        addSerieBtn.addEventListener('click', function() {
            const serieCodigoField = document.getElementById('serieCodigo');
            if (serieCodigoField) serieCodigoField.disabled = false;
        });
    }
    setupConfigModal(
        'seriesModal', 
        'seriesForm', 
        'btnAgregarSerie', 
        'btnEditarSerie', 
        'btnEliminarSerie',
        ['codigo', 'nombre', 'color'], 
        { addBase: '/products/config/series/add', detailsBase: '/products/config/series/details', editBase: '/products/config/series/edit', deleteBase: '/products/config/series/delete' },
        'Serie',
        populateSeriesForm
    );

    // --- Setup for Categories ---
    setupConfigModal(
        'categoryModal', 
        'categoryForm', 
        'btnAgregarCategoria', 
        'btnEditarCategoria', 
        'btnEliminarCategoria',
        ['nombre'], 
        { addBase: '/products/config/categories/add', detailsBase: '/products/config/categories/details', editBase: '/products/config/categories/edit', deleteBase: '/products/config/categories/delete' },
        'Categoría'
    );

    // --- Setup for Marcas ---
    setupConfigModal(
        'marcaModal', 
        'marcaForm', 
        'btnAgregarMarca', 
        'btnEditarMarca', 
        'btnEliminarMarca',
        ['nombre'], 
        { addBase: '/products/config/marcas/add', detailsBase: '/products/config/marcas/details', editBase: '/products/config/marcas/edit', deleteBase: '/products/config/marcas/delete' },
        'Marca'
    );

}); // End DOMContentLoaded
```
