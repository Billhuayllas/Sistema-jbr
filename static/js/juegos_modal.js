document.addEventListener('DOMContentLoaded', function () {
    const juegoModalElement = document.getElementById('juegoModal');
    if (!juegoModalElement) {
        console.warn('Juego modal element not found. Skipping juego modal JS setup.');
        return;
    }
    const juegoModal = new bootstrap.Modal(juegoModalElement);
    const juegoForm = document.getElementById('juegoForm');
    const juegoModalLabel = document.getElementById('juegoModalLabel');
    const juegoIdField = document.getElementById('juegoId');

    // Form fields
    const juegoCodigoField = document.getElementById('juegoCodigo');
    const juegoNombreField = document.getElementById('juegoNombre');

    // Aplicaciones for Juego
    const juegoAplicacionVehiculoField = document.getElementById('juegoAplicacionVehiculo');
    const juegoAplicacionMarcaVehiculoField = document.getElementById('juegoAplicacionMarcaVehiculo');
    const btnAgregarJuegoAplicacion = document.getElementById('btnAgregarJuegoAplicacion');
    const juegoAplicacionesListElement = document.getElementById('juegoAplicacionesList');
    const juegoAplicacionItemTemplate = document.getElementById('juegoAplicacionItemTemplate');
    const emptyJuegoAplicacionesMessage = juegoAplicacionesListElement.querySelector('.empty-juego-aplicaciones');

    // Componentes (Productos) for Juego
    const juegoProductoSelect = $('#juegoProductoSelect'); // jQuery selector for Select2
    const juegoProductoCantidadField = document.getElementById('juegoProductoCantidad');
    const btnAgregarJuegoProducto = document.getElementById('btnAgregarJuegoProducto');
    const juegoProductosListBody = document.getElementById('juegoProductosListBody');
    const juegoProductoItemTemplate = document.getElementById('juegoProductoItemTemplate');
    const emptyJuegoProductosMessage = juegoProductosListBody.querySelector('.empty-juego-productos');

    // Totales Estimados
    const juegoTotalCostoEstimadoElement = document.getElementById('juegoTotalCostoEstimado');
    // const juegoTotalPrecioVentaSugeridoElement = document.getElementById('juegoTotalPrecioVentaSugerido'); // If needed

    let currentJuegoAplicaciones = [];
    let currentJuegoComponentes = []; // Stores {'productoId': id, 'cantidad': qty, 'nombre': name, 'stock': stock, 'costo': cost}

    // Initialize Select2 for product search
    // `all_products_for_select_json` should be passed from the parent template (pc_juegos_list.html)
    // and made available to this script.
    if (typeof all_products_for_select_json !== 'undefined') {
        juegoProductoSelect.select2({
            data: all_products_for_select_json, // `all_products_for_select_json` is the JSON string
            placeholder: "Buscar y seleccionar producto...",
            allowClear: true,
            dropdownParent: $('#juegoModal') // Important for modals
        });
    } else {
        console.warn('`all_products_for_select_json` not defined. Product search in modal will not work.');
    }


    function resetJuegoForm() {
        juegoForm.reset();
        juegoIdField.value = '';
        juegoModalLabel.textContent = 'Agregar Juego de Productos';
        currentJuegoAplicaciones = [];
        currentJuegoComponentes = [];
        renderJuegoAplicaciones();
        renderJuegoComponentes();
        updateJuegoTotales();
        juegoProductoSelect.val(null).trigger('change'); // Reset Select2
        // Activate the first tab (if any tab structure is used inside modal - not explicitly defined in this modal)
    }

    document.getElementById('btnAgregarJuego')?.addEventListener('click', function () {
        resetJuegoForm();
        juegoModal.show();
    });
    
    document.getElementById('btnNuevoJuegoModal')?.addEventListener('click', function() {
        resetJuegoForm();
    });

    // --- Aplicaciones de Vehículo for Juego ---
    function renderJuegoAplicaciones() {
        juegoAplicacionesListElement.innerHTML = ''; // Clear
        if (currentJuegoAplicaciones.length === 0) {
            if(emptyJuegoAplicacionesMessage) emptyJuegoAplicacionesMessage.style.display = 'list-item';
            return;
        }
        if(emptyJuegoAplicacionesMessage) emptyJuegoAplicacionesMessage.style.display = 'none';

        currentJuegoAplicaciones.forEach((app, index) => {
            const clone = juegoAplicacionItemTemplate.content.cloneNode(true);
            clone.querySelector('.juego-aplicacion-vehiculo').textContent = app.vehiculo;
            clone.querySelector('.juego-aplicacion-marcavehiculo').textContent = app.marcaVehiculo;
            clone.querySelector('.remove-juego-aplicacion-btn').dataset.index = index;
            juegoAplicacionesListElement.appendChild(clone);
        });
    }

    if (btnAgregarJuegoAplicacion) {
        btnAgregarJuegoAplicacion.addEventListener('click', function () {
            const vehiculo = juegoAplicacionVehiculoField.value.trim();
            const marcaVehiculo = juegoAplicacionMarcaVehiculoField.value.trim();
            if (vehiculo && marcaVehiculo) {
                currentJuegoAplicaciones.push({ vehiculo, marcaVehiculo });
                renderJuegoAplicaciones();
                juegoAplicacionVehiculoField.value = '';
                juegoAplicacionMarcaVehiculoField.value = '';
            } else {
                Swal.fire('Atención', 'Vehículo y Marca son obligatorios para la aplicación.', 'warning');
            }
        });
    }

    juegoAplicacionesListElement.addEventListener('click', function (event) {
        const targetButton = event.target.closest('.remove-juego-aplicacion-btn');
        if (targetButton) {
            const indexToRemove = parseInt(targetButton.dataset.index, 10);
            currentJuegoAplicaciones.splice(indexToRemove, 1);
            renderJuegoAplicaciones();
        }
    });

    // --- Productos Incluidos (Componentes) for Juego ---
    function updateJuegoTotales() {
        let totalCosto = 0;
        currentJuegoComponentes.forEach(comp => {
            totalCosto += (parseFloat(comp.costo) || 0) * (parseInt(comp.cantidad) || 0);
        });
        juegoTotalCostoEstimadoElement.textContent = `$${totalCosto.toFixed(2)}`;
        // Add logic for precioVentaSugerido if needed
    }

    function renderJuegoComponentes() {
        juegoProductosListBody.innerHTML = ''; // Clear
        if (currentJuegoComponentes.length === 0) {
             if(emptyJuegoProductosMessage) { // Check if the element exists
                const row = emptyJuegoProductosMessage.closest('tr') || emptyJuegoProductosMessage;
                row.style.display = 'table-row'; // Show the "empty" row
            }
            updateJuegoTotales();
            return;
        }
        if(emptyJuegoProductosMessage) {
             const row = emptyJuegoProductosMessage.closest('tr') || emptyJuegoProductosMessage;
             row.style.display = 'none'; // Hide the "empty" row
        }


        currentJuegoComponentes.forEach((comp, index) => {
            const clone = juegoProductoItemTemplate.content.cloneNode(true);
            const cells = clone.querySelectorAll('td');
            cells[0].textContent = `${comp.nombre} (${comp.productoId.substring(0,8)}...)`; // Display name and part of ID
            cells[1].textContent = comp.stock;
            const qtyInput = clone.querySelector('.juego-producto-cantidad');
            qtyInput.value = comp.cantidad;
            qtyInput.dataset.index = index; // For updating quantity
            qtyInput.dataset.productoId = comp.productoId;

            cells[3].textContent = (parseFloat(comp.costo) || 0).toFixed(2);
            cells[4].textContent = ((parseFloat(comp.costo) || 0) * (parseInt(comp.cantidad) || 0)).toFixed(2);
            
            const removeBtn = clone.querySelector('.remove-juego-producto-btn');
            removeBtn.dataset.index = index;
            removeBtn.dataset.productoId = comp.productoId;

            juegoProductosListBody.appendChild(clone);
        });
        updateJuegoTotales();
    }
    
    juegoProductosListBody.addEventListener('change', function(event) {
        if (event.target.classList.contains('juego-producto-cantidad')) {
            const input = event.target;
            const index = parseInt(input.dataset.index, 10);
            const newQuantity = parseInt(input.value, 10);
            if (newQuantity > 0 && index >= 0 && index < currentJuegoComponentes.length) {
                currentJuegoComponentes[index].cantidad = newQuantity;
                renderJuegoComponentes(); // Re-render to update total cost and potentially other things
            } else {
                // Reset to old quantity or handle error
                input.value = currentJuegoComponentes[index].cantidad; 
            }
        }
    });


    if (btnAgregarJuegoProducto) {
        btnAgregarJuegoProducto.addEventListener('click', function () {
            const selectedProductId = juegoProductoSelect.val();
            const cantidad = parseInt(juegoProductoCantidadField.value, 10);

            if (selectedProductId && cantidad > 0) {
                // Check if product already added
                if (currentJuegoComponentes.find(c => c.productoId === selectedProductId)) {
                    Swal.fire('Atención', 'Este producto ya ha sido agregado al juego.', 'warning');
                    return;
                }
                // Find product details from all_products_for_select_json
                const productData = all_products_for_select_json.find(p => p.id === selectedProductId);
                if (productData) {
                    currentJuegoComponentes.push({
                        productoId: productData.id,
                        nombre: productData.text.split(' (')[0], // Extract name
                        stock: productData.stock,
                        costo: productData.cost,
                        cantidad: cantidad
                    });
                    renderJuegoComponentes();
                    juegoProductoSelect.val(null).trigger('change'); // Reset select2
                    juegoProductoCantidadField.value = '1'; // Reset quantity
                } else {
                     Swal.fire('Error', 'Producto no encontrado en los datos cargados.', 'error');
                }
            } else {
                Swal.fire('Atención', 'Seleccione un producto y especifique una cantidad válida.', 'warning');
            }
        });
    }
    
    juegoProductosListBody.addEventListener('click', function (event) {
        const targetButton = event.target.closest('.remove-juego-producto-btn');
        if (targetButton) {
            const indexToRemove = parseInt(targetButton.dataset.index, 10);
            currentJuegoComponentes.splice(indexToRemove, 1);
            renderJuegoComponentes();
        }
    });

    // --- Form Submission (AJAX) ---
    if (juegoForm) {
        juegoForm.addEventListener('submit', function (event) {
            event.preventDefault();
            const juegoId = juegoIdField.value;
            let url = juegoId ? `/products/juegos/edit/${juegoId}` : '/products/juegos/add';
            
            const payload = {
                codigo: juegoCodigoField.value,
                nombre: juegoNombreField.value,
                aplicaciones: currentJuegoAplicaciones,
                componentes: currentJuegoComponentes.map(c => ({ productoId: c.productoId, cantidad: c.cantidad })) // Only send necessary data
            };

            fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    juegoModal.hide();
                    Swal.fire('¡Éxito!', data.message, 'success').then(() => window.location.reload());
                } else {
                    Swal.fire('Error', data.message || 'Ocurrió un error.', 'error');
                }
            })
            .catch(error => {
                console.error('Error submitting juego form:', error);
                Swal.fire('Error', 'Error de conexión o del servidor.', 'error');
            });
        });
    }
    
    // --- Edit Juego: Populate Modal ---
    document.querySelectorAll('.btnEditarJuego').forEach(button => {
        button.addEventListener('click', function() {
            const juegoId = this.dataset.id;
            resetJuegoForm(); // Reset before populating
            juegoIdField.value = juegoId;
            juegoModalLabel.textContent = 'Editar Juego de Productos';

            fetch(`/products/juegos/details/${juegoId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        Swal.fire('Error', data.error, 'error'); return;
                    }
                    juegoCodigoField.value = data.codigo || '';
                    juegoNombreField.value = data.nombre || '';
                    currentJuegoAplicaciones = data.aplicaciones || [];
                    
                    // Populate componentes with full product data for rendering
                    currentJuegoComponentes = [];
                    if (data.componentes && data.componentes.length > 0 && typeof all_products_for_select_json !== 'undefined') {
                        data.componentes.forEach(comp => {
                            const productDetail = all_products_for_select_json.find(p => p.id === comp.productoId);
                            if (productDetail) {
                                currentJuegoComponentes.push({
                                    productoId: comp.productoId,
                                    cantidad: comp.cantidad,
                                    nombre: productDetail.text.split(' (')[0],
                                    stock: productDetail.stock,
                                    costo: productDetail.cost
                                });
                            }
                        });
                    }
                    renderJuegoAplicaciones();
                    renderJuegoComponentes(); // This will also call updateJuegoTotales
                    juegoModal.show();
                })
                .catch(error => Swal.fire('Error', 'No se pudieron cargar los detalles del juego.', 'error'));
        });
    });

    // --- Delete Juego ---
    document.querySelectorAll('.btnEliminarJuego').forEach(button => {
        button.addEventListener('click', function() {
            const juegoId = this.dataset.id;
            Swal.fire({
                title: '¿Está seguro?',
                text: "¡No podrá revertir esta acción!",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Sí, eliminar!',
                cancelButtonText: 'Cancelar'
            }).then((result) => {
                if (result.isConfirmed) {
                    fetch(`/products/juegos/delete/${juegoId}`, { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            Swal.fire('¡Eliminado!', data.message, 'success').then(() => window.location.reload());
                        } else {
                            Swal.fire('Error', data.message || 'No se pudo eliminar el juego.', 'error');
                        }
                    })
                    .catch(error => Swal.fire('Error', 'Error de conexión.', 'error'));
                }
            });
        });
    });
    
    // --- Clone Juego ---
    document.querySelectorAll('.btnClonarJuego').forEach(button => {
        button.addEventListener('click', function() {
            const juegoId = this.dataset.id;
            Swal.fire({
                title: '¿Clonar Juego?',
                text: "Se creará una copia de este juego.",
                icon: 'info',
                showCancelButton: true,
                confirmButtonText: 'Sí, clonar',
                cancelButtonText: 'Cancelar'
            }).then((result) => {
                if (result.isConfirmed) {
                    fetch(`/products/juegos/clone/${juegoId}`, { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            Swal.fire('¡Clonado!', data.message, 'success').then(() => window.location.reload());
                        } else {
                            Swal.fire('Error', data.message || 'No se pudo clonar el juego.', 'error');
                        }
                    })
                    .catch(error => Swal.fire('Error', 'Error de conexión.', 'error'));
                }
            });
        });
    });

}); // End DOMContentLoaded
```
