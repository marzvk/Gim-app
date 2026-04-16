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


    // 2. MANEJO DE MODALES (SOLUCIÓN AL BACKDROP)
    document.body.addEventListener('htmx:afterSwap', function (e) {
        const target = e.detail.target;

        // Solo actuamos si el cambio ocurrió en el contenedor de modales
        if (target.id === 'modal-container') {

            // --- CASO A: El modal se cerró (HTMX devolvió contenido vacío) ---
            if (target.children.length === 0) {
                // A veces Bootstrap no limpia el backdrop si el HTML desaparece muy rápido
                const backdrop = document.querySelector('.modal-backdrop');
                if (backdrop) backdrop.remove();

                // Aseguramos que el body vuelva a ser normal
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
                    backdrop: true, // Asegura que se pueda cerrar clickeando afuera
                    keyboard: true  // Permite cerrar con ESC
                });
                modal.show();

                // Cuando el modal se cierre NATIVAMENTE (clic en X, o clic afuera),
                // limpiamos el contenedor para no dejar basura en el DOM.
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
        // Buscamos si clickeamos en algo con la clase .close-modal (o dentro de ella)
        const btn = e.target.closest('.close-modal');

        if (btn) {
            // Buscamos el contenedor modal más cercano
            const modalEl = btn.closest('.modal');

            if (modalEl) {
                // Obtenemos la instancia de Bootstrap de ese modal
                const modalInstance = bootstrap.Modal.getInstance(modalEl);

                // Si existe, la cerramos elegantemente (esto borra el fondo oscuro automáticamente)
                if (modalInstance) {
                    modalInstance.hide();
                }
            }
        }
    });
});