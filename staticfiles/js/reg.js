document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('registerForm');

    form.addEventListener('submit', function (e) {
        e.preventDefault();

        // Frontend validation: check required fields
        let requiredFields = ['firstname', 'lastname', 'username', 'password', 'email', 'number', 'address', 'state', 'district', 'date_of_birth'];
        let missing = false;

        requiredFields.forEach(field => {
            let value = form.querySelector(`[name="${field}"]`).value.trim();
            if (!value) {
                alert(`Please fill in ${field.replace('_', ' ')}.`);
                missing = true;
                return false;
            }
        });

        if (missing) return; // Stop if missing fields

        // Prepare FormData
        let formData = new FormData(form);

        fetch(form.action || window.location.href, {
            method: "POST",
            headers: {
                "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(data.message);
                window.location.href = "/login/";
            } else {
                alert("Error: " + data.message);
            }
        })
        .catch(error => {
            alert("Something went wrong: " + error);
        });
    });

    // Load districts dynamically when state changes
    const stateSelect = document.getElementById('state');
    const districtSelect = document.getElementById('district');

    stateSelect.addEventListener('change', function () {
        let stateId = this.value;
        districtSelect.innerHTML = '<option value="">Loading...</option>';

        fetch(`/get-districts/${stateId}/`)
            .then(response => response.json())
            .then(data => {
                districtSelect.innerHTML = '<option value="">-- Select District --</option>';
                data.districts.forEach(district => {
                    let option = document.createElement('option');
                    option.value = district.id;
                    option.textContent = district.name;
                    districtSelect.appendChild(option);
                });
            })
            .catch(() => {
                districtSelect.innerHTML = '<option value="">Failed to load</option>';
            });
    });
});
