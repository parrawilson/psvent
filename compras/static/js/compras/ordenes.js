// static/js/compras/ordenes.js



document.addEventListener('DOMContentLoaded', function() {

    
    
    // Seleccionar elementos
    const tbody = document.querySelector('#detalles-table tbody');
    const addButton = document.getElementById('add-detalle');
    const totalForms = document.getElementById('id_form-TOTAL_FORMS');
    let formCount = parseInt(totalForms.value);
    
    
    // Función para actualizar nombres e IDs de los campos
    function updateFormIndexes(row, index) {
        const inputs = row.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            const name = input.name.replace(/form-\d+-/, `form-${index}-`);
            input.name = name;
            if (input.id) {
                input.id = input.id.replace(/id_form-\d+-/, `id_form-${index}-`);
            }
        });
        const labels = row.querySelectorAll('label');
        labels.forEach(label => {
            if (label.htmlFor) {
                label.htmlFor = label.htmlFor.replace(/id_form-\d+-/, `id_form-${index}-`);
            }
        });
    }
    
    // Función para clonar una fila
    function cloneRow() {
        alert('estoy en la función clonar');
        const emptyRow = tbody.querySelector('.detalle-form');
        if (!emptyRow) return;
        
        const newRow = emptyRow.cloneNode(true);
        formCount++;
        
        // Actualizar índices
        updateFormIndexes(newRow, formCount - 1); // -1 porque empieza en 0
        
        // Limpiar valores
        newRow.querySelector('[id$="-producto"]').value = '';
        newRow.querySelector('[id$="-cantidad"]').value = '1';
        newRow.querySelector('[id$="-precio_unitario"]').value = '0.00';
        newRow.querySelector('[id$="-subtotal"]').value = '0.00';
        newRow.querySelector('[id$="-DELETE"]').checked = false;
        
        // Añadir al final
        tbody.appendChild(newRow);
        totalForms.value = formCount;
    }
    
    // Calcular subtotales
    function calcularSubtotales() {
        const rows = tbody.querySelectorAll('.detalle-form');
        rows.forEach(row => {
            const cantidad = parseFloat(row.querySelector('[id$="-cantidad"]').value) || 0;
            const precio = parseFloat(row.querySelector('[id$="-precio_unitario"]').value) || 0;
            const subtotal = cantidad * precio;
            row.querySelector('[id$="-subtotal"]').value = subtotal.toFixed(2);
        });
    }
    
    // Evento para el botón agregar
    addButton.addEventListener('click', function(e) {
        e.preventDefault();
        cloneRow();
    });
    
    // Evento para cambios en cantidad y precio
    tbody.addEventListener('input', function(e) {
        if (e.target.name.includes('cantidad') || e.target.name.includes('precio_unitario')) {
            calcularSubtotales();
        }
    });
    
    // Inicializar cálculo de subtotales
    calcularSubtotales();
});

