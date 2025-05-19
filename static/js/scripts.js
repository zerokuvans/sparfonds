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
            const rate = parseFloat(interestRate.value) / 100 / 12; // Tasa mensual
            const time = parseInt(loanTerm.value); // Meses
            
            // Calcular pago mensual
            const x = Math.pow(1 + rate, time);
            const monthly = (principal * x * rate) / (x - 1);
            
            if (isFinite(monthly)) {
                // Mostrar resultados
                monthlyPayment.innerHTML = monthly.toFixed(2);
                totalPayment.innerHTML = (monthly * time).toFixed(2);
                totalInterest.innerHTML = ((monthly * time) - principal).toFixed(2);
                
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