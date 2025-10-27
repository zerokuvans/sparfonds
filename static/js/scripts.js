// Scripts para SparFonds

document.addEventListener('DOMContentLoaded', function() {
    // Calculadora de préstamos
    const loanCalculator = document.getElementById('loan-calculator');
    if (loanCalculator) {
        const calculateBtn = document.getElementById('calculate-loan');
        const loanAmount = document.getElementById('loan-amount');
        const interestRate = document.getElementById('interest-rate');
        const loanTerm = document.getElementById('loan-term');
        const resultDiv = document.getElementById('loan-result');
        const monthlyPayment = document.getElementById('monthly-payment');
        const totalPayment = document.getElementById('total-payment');
        const totalInterest = document.getElementById('total-interest');
        
        calculateBtn.addEventListener('click', function() {
            // Obtener valores
            const principal = parseFloat(loanAmount.value);
            const annualRate = parseFloat(interestRate.value) / 100; // Tasa anual
            const time = parseInt(loanTerm.value); // Meses
            
            // NUEVO SISTEMA: Interés Simple Anualizado
            // Calcular interés mensual fijo: (monto * tasa_anual) / 12
            const monthlyInterest = (principal * annualRate) / 12;
            
            // Calcular cuota de capital mensual: monto / plazo
            const monthlyCapital = principal / time;
            
            // Cuota total mensual: capital + interés fijo
            const monthly = monthlyCapital + monthlyInterest;
            
            // Total de intereses: interés mensual * plazo
            const totalInterestAmount = monthlyInterest * time;
            
            // Total a pagar: monto + total intereses
            const totalPaymentAmount = principal + totalInterestAmount;
            
            if (isFinite(monthly) && monthly > 0) {
                // Mostrar resultados
                monthlyPayment.innerHTML = monthly.toFixed(2);
                totalPayment.innerHTML = totalPaymentAmount.toFixed(2);
                totalInterest.innerHTML = totalInterestAmount.toFixed(2);
                
                // Agregar información adicional del nuevo sistema
                const additionalInfo = document.getElementById('additional-info');
                if (additionalInfo) {
                    additionalInfo.innerHTML = `
                        <div class="alert alert-info mt-3">
                            <h6><i class="fas fa-info-circle"></i> Sistema de Interés Simple Anualizado</h6>
                            <p class="mb-1"><strong>Cuota de capital mensual:</strong> $${monthlyCapital.toFixed(2)}</p>
                            <p class="mb-1"><strong>Interés mensual fijo:</strong> $${monthlyInterest.toFixed(2)}</p>
                            <p class="mb-0"><small class="text-muted">El interés se mantiene constante durante todo el plazo, calculado sobre el monto inicial.</small></p>
                        </div>
                    `;
                }
                
                // Mostrar resultados
                resultDiv.classList.add('show');
            } else {
                alert('Por favor, ingrese valores válidos.');
            }
        });
    }
    
    // Animación para tarjetas
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.classList.add('fade-in');
    });
    
    // Formatear montos como moneda
    const formatCurrency = () => {
        const currencyElements = document.querySelectorAll('.currency');
        currencyElements.forEach(element => {
            const value = parseFloat(element.textContent);
            if (!isNaN(value)) {
                element.textContent = new Intl.NumberFormat('es-MX', {
                    style: 'currency',
                    currency: 'MXN'
                }).format(value);
            }
        });
    };
    
    formatCurrency();
    
    // Validación de formularios
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
});