function Terug() {
    window.location.href = '/';
  }

// Alert thingy
setTimeout(function() {
    var alertRow = document.getElementById('alertRow');
    var alert = document.getElementById('warningAlert');
    if (alert) {
        alert.classList.remove('show');
        alert.classList.add('fade');
        alert.style.transition = "opacity 0.5s ease";
        alert.style.opacity = 0;
        setTimeout(function() {
            alertRow.remove();
        }, 500);
    }
}, 5000);

// the uh, reset button thingy
document.getElementById('resetButton').addEventListener('click', function() {
    // Reset all inputs
    document.querySelector('input[name="name"]').value = '';

    document.querySelector('select[name="attendance"]').value = '';

    document.querySelector('input[name="start_date"]').value = '';
    document.querySelector('input[name="end_date"]').value = '';
    
    this.form.submit();
});