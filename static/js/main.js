document.addEventListener('DOMContentLoaded', () => {

    // 1. MANEJO DE TOASTS (Notificaciones)
    window.showToast = function (message, type = 'success') {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) return;

        let icon = type === 'success' ? 'bi-check-circle-fill' :
            type === 'error' ? 'bi-exclamation-triangle-fill' : 'bi-info-circle-fill';
        let bgClass = type === 'success' ? 'text-bg-success' :
            type === 'error' ? 'text-bg-danger' : 'text-bg-primary';

        const html = `
            <div class="toast align-items-center ${bgClass} border-0 mb-2" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="bi ${icon} me-2"></i> ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;

        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        const toastEl = tempDiv.firstElementChild;

        toastContainer.appendChild(toastEl);
        const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
        toast.show();

        toastEl.addEventListener('hidden.bs.toast', () => {
            toastEl.remove();
        });
    };

    document.body.addEventListener('showToast', (e) => {
        window.showToast(e.detail.message, e.detail.type);
    });


    // ----------------------------------------------------
    // --- NUEVO: FIX PARA CIERRE DE MODALES (STATUS 204) ---
    // ----------------------------------------------------
    // Esto intercepta la respuesta ANTES de que HTMX toque el HTML.
    // Si el servidor dice "Guardado" (204 o 200 vacío), le pedimos a Bootstrap
    // que cierre el modal suavemente. Su lógica interna se encarga de borrar el fondo oscuro.
    document.body.addEventListener('htmx:beforeSwap', function (evt) {
        if (evt.detail.target.id === 'modal-container') {
            const status = evt.detail.xhr.status;
            const responseText = evt.detail.xhr.responseText;

            // Detectar respuesta exitosa vacía
            if (status === 204 || (status === 200 && responseText.trim() === "")) {
                evt.preventDefault(); // Decimos: "HTMX, NO borres el HTML aún"

                // Buscamos el modal visible actualmente
                const modalEl = document.querySelector('#modal-container .modal');
                if (modalEl) {
                    const modalInstance = bootstrap.Modal.getInstance(modalEl);
                    if (modalInstance) {
                        modalInstance.hide(); // Bootstrap cierra (animación + backdrop)
                        // El listener 'hidden.bs.modal' que ya tenes abajo se encargará del innerHTML=''
                    }
                }
            }
        }
    });


    // 2. MANEJO DE MODALES (SOLUCIÓN AL BACKDROP Y APERTURA)
    document.body.addEventListener('htmx:afterSwap', function (e) {
        const target = e.detail.target;

        // Solo actuamos si el cambio ocurrió en el contenedor de modales
        if (target.id === 'modal-container') {

            // --- CASO A: El modal se cerró (Contenedor vacío por limpieza manual) ---
            // Esto queda como respaldo por si el evento 'hidden.bs.modal' falla en limpiar
            if (target.children.length === 0) {
                const backdrop = document.querySelector('.modal-backdrop');
                if (backdrop) backdrop.remove();
                document.body.classList.remove('modal-open');
                document.body.style.overflow = '';
                document.body.style.paddingRight = '';
                return;
            }

            // --- CASO B: Se abrió un nuevo modal (HTMX devolvió HTML con <div class="modal">) ---
            const modalEl = target.firstElementChild;
            if (modalEl && modalEl.classList.contains('modal')) {
                // Inicializamos el modal de Bootstrap
                const modal = new bootstrap.Modal(modalEl, {
                    backdrop: true,
                    keyboard: true
                });
                modal.show();

                // Limpieza al cerrar: Borra el HTML cuando Bootstrap termina de ocultarlo
                modalEl.addEventListener('hidden.bs.modal', function () {
                    target.innerHTML = '';
                    modal.dispose();
                });
            }
        }
    });


    // 3. SPINNER GLOBAL
    document.body.addEventListener('htmx:beforeRequest', (evt) => {
        const spinner = document.getElementById('global-spinner');
        if (spinner) {
            setTimeout(() => {
                if (evt.detail.xhr.readyState < 4) spinner.style.display = 'block';
            }, 300);
        }
    });

    document.body.addEventListener('htmx:afterRequest', (evt) => {
        const spinner = document.getElementById('global-spinner');
        if (spinner) spinner.style.display = 'none';
    });


    // 4. MANEJO MANUAL DE CLASE "close-modal"
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('.close-modal');
        if (btn) {
            const modalEl = btn.closest('.modal');
            if (modalEl) {
                const modalInstance = bootstrap.Modal.getInstance(modalEl);
                if (modalInstance) {
                    modalInstance.hide();
                }
            }
        }
    });
});