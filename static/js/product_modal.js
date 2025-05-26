document.addEventListener('DOMContentLoaded', function () {
    const productModalElement = document.getElementById('productModal');
    if (!productModalElement) {
        console.error('Product modal element not found.');
        return;
    }
    const productModal = new bootstrap.Modal(productModalElement); // Ensure Bootstrap 5 JS is loaded

    const productForm = document.getElementById('productForm');
    const modalTitle = document.getElementById('productModalLabel');
    const productIdField = document.getElementById('productId');

    // Form fields (main tab)
    const productCodeField = document.getElementById('productCode');
    const productNameField = document.getElementById('productName');
    const productBrandField = document.getElementById('productBrand');
    const productCategoryField = document.getElementById('productCategory');
    const productSeriesField = document.getElementById('productSeries');
    const productMeasureField = document.getElementById('productMeasure');
    const productStockField = document.getElementById('productStock');
    const productCostField = document.getElementById('productCost');
    const productPriceUnitField = document.getElementById('productPriceUnit');
    const productPriceWholesaleField = document.getElementById('productPriceWholesale');
    const productDescriptionField = document.getElementById('productDescription');

    // Image tab fields
    const imageInputs = [];
    const imagePreviews = [];
    const removeImageBtns = [];
    const currentImageFilenameFields = [];
    const removeImageCheckboxes = [];

    for (let i = 1; i <= 5; i++) {
        imageInputs.push(document.getElementById(`productImage${i}`));
        imagePreviews.push(document.getElementById(`imagePreview${i}`));
        removeImageBtns.push(document.getElementById(`removeImageBtn${i-1}`) || document.querySelector(`.remove-image-btn[data-slot="${i-1}"]`)); // Ensure correct selector
        currentImageFilenameFields.push(document.getElementById(`currentImageFilename${i-1}`));
        removeImageCheckboxes.push(document.getElementById(`removeImage${i-1}`));
    }
    
    // Aplicaciones tab fields
    const vehicleInputField = document.getElementById('vehicleInput');
    const brandInputAplicacionField = document.getElementById('brandInputAplicacion');
    const gameCodeInputField = document.getElementById('gameCodeInput');
    const gameNameInputField = document.getElementById('gameNameInput');
    const addApplicationBtn = document.getElementById('addApplicationBtn');
    const applicationsListElement = document.getElementById('applicationsList');
    const aplicacionItemTemplate = document.getElementById('aplicacionItemTemplate');
    const emptyAplicacionesMessage = applicationsListElement.querySelector('.empty-aplicaciones');

    let aplicaciones = []; // Array to store current aplicaciones for the product

    function resetForm() {
        productForm.reset();
        productIdField.value = '';
        modalTitle.textContent = 'Agregar Producto';
        
        // Reset image previews and hidden fields
        for (let i = 0; i < 5; i++) {
            if (imagePreviews[i]) imagePreviews[i].style.display = 'none';
            if (imagePreviews[i]) imagePreviews[i].src = '#';
            if (removeImageBtns[i]) removeImageBtns[i].style.display = 'none';
            if (currentImageFilenameFields[i]) currentImageFilenameFields[i].value = '';
            if (removeImageCheckboxes[i]) {
                 removeImageCheckboxes[i].checked = false;
                 removeImageCheckboxes[i].style.display = 'none'; // Hide checkbox
            }
            if (imageInputs[i]) imageInputs[i].value = ''; // Clear file input
        }

        // Reset aplicaciones
        aplicaciones = [];
        renderAplicaciones();
        
        // Activate the first tab
        const firstTabButton = document.querySelector('#productModalTabs button');
        if (firstTabButton) {
            const tab = new bootstrap.Tab(firstTabButton);
            tab.show();
        }
    }

    // Open modal for "Add Product"
    document.getElementById('addProductoBtn')?.addEventListener('click', function () {
        resetForm();
        productModal.show();
    });
    document.getElementById('btnNuevoProductoModal')?.addEventListener('click', function() {
        resetForm(); // Keep modal open, just reset form for new entry
    });


    // Open modal for "Edit Product"
    document.querySelectorAll('.edit-product, .product-actions a.btn-warning').forEach(button => {
        button.addEventListener('click', function (event) {
            event.preventDefault(); // Prevent default link behavior if it's an <a> tag
            const productId = this.dataset.id || this.closest('.product-card')?.dataset.id || this.closest('tr')?.dataset.id;
            if (!productId) {
                console.error('Product ID not found for edit button.');
                Swal.fire('Error', 'No se pudo obtener el ID del producto.', 'error');
                return;
            }

            resetForm(); // Reset form before populating
            modalTitle.textContent = 'Editar Producto';
            productIdField.value = productId;

            fetch(`/products/details/${productId}/`)
                .then(response => {
                    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                    return response.json();
                })
                .then(productData => {
                    if (productData.error) {
                        Swal.fire('Error', productData.error, 'error');
                        return;
                    }
                    // Populate main form fields
                    productCodeField.value = productData.product_code || '';
                    productNameField.value = productData.name || '';
                    productBrandField.value = productData.brand_code || '';
                    productCategoryField.value = productData.category_code || '';
                    productSeriesField.value = productData.series || '';
                    productMeasureField.value = productData.measurement || '';
                    productStockField.value = productData.stock !== null ? productData.stock : '';
                    productCostField.value = productData.cost !== null ? productData.cost : '';
                    productPriceUnitField.value = productData.price_unit !== null ? productData.price_unit : '';
                    productPriceWholesaleField.value = productData.price_wholesale !== null ? productData.price_wholesale : '';
                    productDescriptionField.value = productData.description || '';

                    // Populate image previews and hidden fields
                    const filenames = productData.image_filenames || [null]*5;
                    for (let i = 0; i < 5; i++) {
                        if (filenames[i]) {
                            imagePreviews[i].src = `/static/uploads/products/${filenames[i]}`;
                            imagePreviews[i].style.display = 'block';
                            removeImageBtns[i].style.display = 'inline-block';
                            currentImageFilenameFields[i].value = filenames[i];
                            removeImageCheckboxes[i].style.display = 'inline-block'; // Show checkbox
                        } else {
                            imagePreviews[i].style.display = 'none';
                            imagePreviews[i].src = '#';
                            removeImageBtns[i].style.display = 'none';
                            currentImageFilenameFields[i].value = '';
                            removeImageCheckboxes[i].style.display = 'none'; // Hide checkbox
                        }
                        imageInputs[i].value = ''; // Clear file input
                        removeImageCheckboxes[i].checked = false; // Uncheck remove checkbox
                    }
                    
                    // Populate aplicaciones
                    aplicaciones = productData.aplicaciones || [];
                    renderAplicaciones();

                    productModal.show();
                })
                .catch(error => {
                    console.error('Error fetching product details:', error);
                    Swal.fire('Error', 'No se pudieron cargar los detalles del producto. ' + error.message, 'error');
                });
        });
    });

    // Image Preview and Remove Logic
    for (let i = 0; i < 5; i++) {
        if (imageInputs[i]) {
            imageInputs[i].addEventListener('change', function () {
                const file = this.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = function (e) {
                        imagePreviews[i].src = e.target.result;
                        imagePreviews[i].style.display = 'block';
                        removeImageBtns[i].style.display = 'inline-block';
                        currentImageFilenameFields[i].value = ''; // New file selected, clear current filename
                        removeImageCheckboxes[i].checked = false; // Uncheck remove if new file is chosen
                        removeImageCheckboxes[i].style.display = 'inline-block';
                    }
                    reader.readAsDataURL(file);
                }
            });
        }

        if (removeImageBtns[i]) {
            removeImageBtns[i].addEventListener('click', function () {
                imageInputs[i].value = ''; // Clear the file input
                imagePreviews[i].src = '#';
                imagePreviews[i].style.display = 'none';
                this.style.display = 'none'; // Hide remove button itself
                // If there was a current image, mark it for removal
                if (currentImageFilenameFields[i].value) {
                    removeImageCheckboxes[i].checked = true;
                }
                // currentImageFilenameFields[i].value = ''; // Keep current filename for server to know which one to delete if editing
            });
        }
    }

    // Aplicaciones (Legado) Tab Logic
    function renderAplicaciones() {
        applicationsListElement.innerHTML = ''; // Clear current list
        if (aplicaciones.length === 0) {
            if(emptyAplicacionesMessage) emptyAplicacionesMessage.style.display = 'list-item';
            return;
        }
         if(emptyAplicacionesMessage) emptyAplicacionesMessage.style.display = 'none';

        aplicaciones.forEach((app, index) => {
            const clone = aplicacionItemTemplate.content.cloneNode(true);
            clone.querySelector('.aplicacion-vehiculo').textContent = app.vehiculo;
            clone.querySelector('.aplicacion-marca').textContent = app.marca;
            clone.querySelector('.aplicacion-codigojuego').textContent = app.codigoJuego;
            clone.querySelector('.aplicacion-nombrejuego').textContent = app.nombreJuego;
            clone.querySelector('.remove-aplicacion-btn').dataset.index = index;
            applicationsListElement.appendChild(clone);
        });
    }

    if (addApplicationBtn) {
        addApplicationBtn.addEventListener('click', function () {
            const vehiculo = vehicleInputField.value.trim();
            const marca = brandInputAplicacionField.value.trim();
            const codigoJuego = gameCodeInputField.value.trim();
            const nombreJuego = gameNameInputField.value.trim();

            if (vehiculo && marca) { // Basic validation
                aplicaciones.push({ vehiculo, marca, codigoJuego, nombreJuego });
                renderAplicaciones();
                // Clear input fields
                vehicleInputField.value = '';
                brandInputAplicacionField.value = '';
                gameCodeInputField.value = '';
                gameNameInputField.value = '';
            } else {
                Swal.fire('Atención', 'Vehículo y Marca son obligatorios para agregar una aplicación.', 'warning');
            }
        });
    }

    applicationsListElement.addEventListener('click', function (event) {
        if (event.target.classList.contains('remove-aplicacion-btn') || event.target.closest('.remove-aplicacion-btn')) {
            const button = event.target.classList.contains('remove-aplicacion-btn') ? event.target : event.target.closest('.remove-aplicacion-btn');
            const indexToRemove = parseInt(button.dataset.index, 10);
            aplicaciones.splice(indexToRemove, 1);
            renderAplicaciones();
        }
    });

    // Form Submission (AJAX)
    if (productForm) {
        productForm.addEventListener('submit', function (event) {
            event.preventDefault();

            const formData = new FormData(productForm);
            const productId = productIdField.value;
            let url = '/products/add/';
            if (productId) {
                url = `/products/edit/${productId}/`;
            }
            
            // Append aplicaciones data as JSON string
            formData.append('aplicaciones_data', JSON.stringify(aplicaciones));

            // Append current image filenames for edit, so server knows what was there
            if (productId) { // Only for edit
                for(let i=0; i<5; i++){
                    if(currentImageFilenameFields[i] && currentImageFilenameFields[i].value) {
                        formData.append(`currentImageFilename${i}`, currentImageFilenameFields[i].value);
                    }
                    // The 'removeImageX' checkbox value is already part of FormData if checked
                }
            }


            fetch(url, {
                method: 'POST',
                body: formData // FormData handles multipart/form-data for file uploads
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    productModal.hide();
                    Swal.fire({
                        title: '¡Éxito!',
                        text: data.message,
                        icon: 'success',
                        timer: 2000,
                        showConfirmButton: false
                    }).then(() => {
                        window.location.reload(); // Simple refresh to show changes
                    });
                } else {
                    Swal.fire('Error', data.message || 'Ocurrió un error.', 'error');
                }
            })
            .catch(error => {
                console.error('Error submitting form:', error);
                Swal.fire('Error', 'Error de conexión o del servidor.', 'error');
            });
        });
    }

    // Make sure Select2 is initialized if used on dropdowns within the modal
    // Example: $('#productBrand').select2({ dropdownParent: $('#productModal') });
    // This needs to be done *after* the modal is shown or if it's always in DOM.
    // For simplicity, assuming standard select for now.
});
```
