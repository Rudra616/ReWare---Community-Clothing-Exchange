function refreshCaptcha(button) {
    const url = button.dataset.url; // Get URL from button
    fetch(url)
        .then(response => response.json())
        .then(data => {
            document.querySelector('.cpatchur').textContent = data.captcha_code;
        })
        .catch(error => {
            console.error('Error refreshing captcha:', error);
        });
}


function required() {
  var isValid = true;
  var errors = document.querySelectorAll("[class='error']");
  var name = document.getElementById("name").value.trim();
  var password = document.getElementById("password").value.trim();
  var captcha = document.getElementById("captcha").value.trim();
  var all = [name, password, captcha];
  all.forEach((element, key) => {
    if (element === "") {
      errors[key].innerText = "This field is required";
      isValid = false;
    }
  });
  return isValid;
}