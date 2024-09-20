
let reload_interval = null;
let time = null;
let time_value = ""; 
function convertUTCDateToLocalDate(date) {
    var newDate = new Date(date.getTime() + date.getTimezoneOffset() * 60 * 1000);

    var offset = date.getTimezoneOffset() / 60;
    var hours = date.getHours();

    newDate.setHours(hours - offset);

    return newDate;
}

function getStateName(state){
    let retorno = "";
    switch(state){
        case "in_process":
            retorno = "En Proceso";
            break;
            case "no_executed":
            retorno = "No Ejecutado";
            break;
            case "in_queue":
            retorno = "En Cola";
            break;
    }

    return retorno;

}

document.getElementById('reload-button').addEventListener('click', () => {
    window.electron.recargar(time_value).then((reload_time) => {
        window.electron.getConciliaciones().then((conciliaciones) => {
            let tbodyRef = document.getElementById('conciliaciones').getElementsByTagName('tbody')[0];
            
            tbodyRef.innerHTML = "";

            for (let x of conciliaciones) {

                const newRow = tbodyRef.insertRow();
                newRow.insertCell().appendChild(document.createTextNode(x.name));
                newRow.insertCell().appendChild(document.createTextNode(getStateName(x.state)));
                newRow.insertCell().appendChild(document.createTextNode(moment(x.date).isValid() ? moment(convertUTCDateToLocalDate(new Date(x.date))).format("DD/MM/YYYY HH:mm:ss") : ""));
                newRow.insertCell().appendChild(document.createTextNode(moment(x.date_end).isValid() ? moment(convertUTCDateToLocalDate(new Date(x.date_end))).format("DD/MM/YYYY HH:mm:ss") : ""));

                if (x.state == "no_executed") {
                    const buttonConciliar = document.createElement("button");
                    buttonConciliar.className = "btn btn-primary";
                    buttonConciliar.textContent = "Conciliar"
                    buttonConciliar.addEventListener("click", () => {
                        document.getElementById("cover-spin").style.display = "inline";
                        window.electron.conciliar_diario(time_value, x.journal, x.fecha_corte).then(()=>{
                            setTimeout(() => {
                                document.getElementById('reload-button').click();    
                            }, 100);
                            
                        });
                        
                    });
                    newRow.insertCell().appendChild(buttonConciliar);
                } else {
                    newRow.insertCell().appendChild(document.createTextNode(""));
                }


                // Append a text node to the cell



            }
            document.getElementById("cover-spin").style.display = "none";
            document.getElementById("reload-every").value = time_value;

        });



    });


});

window.addEventListener('DOMContentLoaded', () => {
    document.getElementById("cover-spin").style.display = "inline";
    document.getElementById('reload-button').click();
});

document.getElementById('reload-every').addEventListener('change', (e) => {

    console.log(e.target.value);
    time_value = e.target.value;
    time = null;
    clearInterval(reload_interval);
    if (e.target.value.indexOf("s") >= 0) {

        time = parseInt(e.target.value.replace("s", ""), 10) * 1000;

    } else if (e.target.value.indexOf("m") >= 0) {
        time = parseInt(e.target.value.replace("s", ""), 10) * 60 * 1000;
    } else if (e.target.value.indexOf("h") >= 0) {
        time = parseInt(e.target.value.replace("h", ""), 10) * 60 * 60 * 1000;
    } else {
        time = null;
    }

    if (time !== null) {
        reload_interval = setInterval(() => {

            document.getElementById('reload-button').click();

        }, time);
    } else {
        clearInterval(reload_interval);
    }

});
