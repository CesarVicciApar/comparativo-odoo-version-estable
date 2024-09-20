document.querySelector("#login-button").addEventListener("click", () => {
    document.getElementById("error-message").innerHTML = "";
    document.getElementById("cover-spin").style.display = "inline";
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    const servidor = document.getElementById("server").value;

    const data = {
        username: username,
        password: password,
        servidor: servidor
    };

    window.electron.login(data);
});