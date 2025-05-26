document.addEventListener('DOMContentLoaded', function() {
    const importForm = document.getElementById('importBackupForm');
    const fileInput = document.getElementById('backup-importar-general-file');
    // const importButton = document.getElementById('btnImportarBackup'); // Not strictly needed if listening to form submit

    if (importForm && fileInput) { // Check for fileInput as well
        importForm.addEventListener('submit', function(event) {
            event.preventDefault();
            if (!fileInput.files || fileInput.files.length === 0) {
                Swal.fire('Atención', 'Por favor, seleccione un archivo de backup para importar.', 'warning');
                return;
            }

            const formData = new FormData();
            formData.append('backup_file', fileInput.files[0]);

            Swal.fire({
                title: '¿Restaurar Backup?',
                html: "Está a punto de reemplazar todos los datos del sistema con el contenido de este archivo de backup. <br><strong class='text-danger'>¡Esta acción no se puede deshacer!</strong><br>¿Desea continuar?",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Sí, Restaurar Ahora',
                cancelButtonText: 'Cancelar',
                customClass: {
                    title: 'swal2-title-custom', 
                }
            }).then((result) => {
                if (result.isConfirmed) {
                    Swal.fire({
                        title: 'Procesando...',
                        text: 'Restaurando datos desde el backup. Por favor espere.',
                        allowOutsideClick: false,
                        didOpen: () => {
                            Swal.showLoading();
                        }
                    });

                    // The URL is hardcoded here. If using Flask's url_for in JS, it needs to be passed from template.
                    // Assuming '/backup/import_all_data' is the correct static URL.
                    // For dynamic URL generation:
                    // const importUrl = importForm.dataset.importUrl; // e.g. <form data-import-url="{{ url_for(...) }}">
                    // For now, using the path directly as it was in the template.
                    // Note: This direct path might not work if the app is hosted under a subpath.
                    // It's better practice to pass this URL from the template to the JS.
                    // However, the original template had "{{ url_for('backup_bp.import_all_data_route') }}" directly in fetch.
                    // Since this JS file is static, it can't use Jinja.
                    // This URL needs to be fixed or passed via data attribute.
                    // For now, I will use a relative path, assuming backup_bp is at /backup.
                    
                    let importUrl = '/backup/import_all_data'; 
                    // A robust way: get the base URL if app is not at root
                    // Or, the form action could be set to the url_for and then use form.action
                    if (importForm.action && importForm.action !== window.location.href) { // Check if action is set and not just current page
                        importUrl = importForm.action;
                    }


                    fetch(importUrl, { // Using the form's action attribute if available
                        method: 'POST',
                        body: formData
                    })
                    .then(response => response.json())
                    .then(data => {
                        Swal.close(); 
                        fileInput.value = ''; // Clear the file input
                        if (data.success) {
                            Swal.fire('¡Restauración Completa!', data.message, 'success')
                                .then(() => window.location.reload()); 
                        } else {
                            Swal.fire('Error en la Restauración', data.message || 'Ocurrió un error desconocido.', 'error');
                        }
                    })
                    .catch(error => {
                        Swal.close(); 
                        fileInput.value = ''; // Clear the file input
                        console.error('Error during import:', error);
                        Swal.fire('Error de Red', 'No se pudo conectar con el servidor o hubo un error en la solicitud.', 'error');
                    });
                } else {
                    fileInput.value = ''; // Clear file input if user cancels confirmation
                }
            });
        });
    }

    // Optional Enhancement for Export Button
    const exportButton = document.getElementById('backup-exportar-general');
    if (exportButton) {
        exportButton.addEventListener('click', function(event) {
            event.preventDefault(); // Stop direct navigation
            const exportUrl = this.href;

            Swal.fire({
                title: 'Confirmar Exportación',
                text: 'Se generará y descargará un archivo JSON con todos los datos del sistema. El proceso puede tardar unos momentos.',
                icon: 'info',
                showCancelButton: true,
                confirmButtonText: 'Sí, Exportar',
                cancelButtonText: 'Cancelar'
            }).then((result) => {
                if (result.isConfirmed) {
                    // Show a brief "preparing download" message
                    Swal.fire({
                        title: 'Preparando Descarga...',
                        text: 'Su archivo se descargará en breve.',
                        icon: 'info',
                        timer: 2000, // Auto-close after 2 seconds
                        showConfirmButton: false,
                        allowOutsideClick: false
                    });
                    window.location.href = exportUrl; // Proceed with download
                }
            });
        });
    }
});
```
