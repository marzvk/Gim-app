document.addEventListener('DOMContentLoaded', () => {

    // ─── TOASTS ───────────────────────────────────────────────────────────────
    window.showToast = function (message, type = 'success') {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) return;

        const icon = type === 'success' ? 'bi-check-circle-fill'
            : type === 'error' ? 'bi-exclamation-triangle-fill'
                : 'bi-info-circle-fill';
        const bgClass = type === 'success' ? 'text-bg-success'
            : type === 'error' ? 'text-bg-danger'
                : 'text-bg-primary';

        const html = `
            <div class="toast align-items-center ${bgClass} border-0 mb-2"
                 role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="bi ${icon} me-2"></i>${message}
                    </div>
                    <button type="button"
                            class="btn-close btn-close-white me-2 m-auto"
                            data-bs-dismiss="toast"
                            aria-label="Cerrar"></button>
                </div>
            </div>`;

        const temp = document.createElement('div');
        temp.innerHTML = html;
        const toastEl = temp.firstElementChild;
        toastContainer.appendChild(toastEl);

        const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
        toast.show();
        toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
    };

    document.body.addEventListener('showToast', (e) => {
        window.showToast(e.detail.message, e.detail.type);
    });


    // ─── MODAL SHELL ──────────────────────────────────────────────────────────
    const shellEl = document.getElementById('modal-shell');

    // Si no existe el shell (páginas sin modal, ej: reportes), no hacemos nada
    if (shellEl) {
        const shellModal = new bootstrap.Modal(shellEl, { keyboard: true });

        // Después de cada swap de HTMX en #modal-container:
        // Si hay contenido → abrir. Si quedó vacío → cerrar.
        document.body.addEventListener('htmx:afterSwap', function (evt) {
            if (evt.detail.target.id !== 'modal-container') return;

            const hasContent = evt.detail.target.children.length > 0;

            if (hasContent) {
                // Soporte para modal-lg: el modal-content puede tener data-modal-size
                const content = evt.detail.target.firstElementChild;
                const newSize = content ? content.dataset.modalSize : null;
                const dialogEl = document.getElementById('modal-dialog');
                dialogEl.classList.remove('modal-sm', 'modal-lg', 'modal-xl');
                if (newSize) dialogEl.classList.add(newSize);

                shellModal.show();
            } else {
                shellModal.hide();
            }
        });

        // Cuando Bootstrap termina de cerrar el shell: limpiar el contenido interno
        shellEl.addEventListener('hidden.bs.modal', function () {
            document.getElementById('modal-container').innerHTML = '';
        });

        // Botones .close-modal: cerrar el shell
        document.addEventListener('click', function (e) {
            if (e.target.closest('.close-modal')) {
                shellModal.hide();
            }
        });

        // Respuesta 204 o 200 vacío = guardado exitoso, cerrar modal
        document.body.addEventListener('htmx:beforeSwap', function (evt) {
            if (evt.detail.target.id !== 'modal-container') return;

            const status = evt.detail.xhr.status;
            if (status === 204 || (status === 200 && evt.detail.xhr.responseText.trim() === '')) {
                evt.preventDefault();
                shellModal.hide();
            }
        });
    }


    // ─── SPINNER GLOBAL ───────────────────────────────────────────────────────
    document.body.addEventListener('htmx:beforeRequest', () => {
        const spinner = document.getElementById('global-spinner');
        if (spinner) spinner.style.display = 'block';
    });
    document.body.addEventListener('htmx:afterRequest', () => {
        const spinner = document.getElementById('global-spinner');
        if (spinner) spinner.style.display = 'none';
    });

});