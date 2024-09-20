const conciliacion = require("../conciliacion/procesar");
const config = require("../config");
exports.runConciliacion = async (req, res) => {
    if (!req.body.diario || !req.body.fecha_corte, !req.body.execution_key) {
        res.status(400).send({
            message: "Diario,fecha de corte y llave de ejecución son obligatorios"
        });
        return;
    }else if(!config.getValidJournals().includes(parseInt(req.body.diario,10))){
        res.status(400).send({
            message: `El diario ${req.body.diario} no está dentro de las opciones disponibles para conciliación bancaria`
        }); 
        return;
    }

    conciliacion.procesar(parseInt(req.body.diario,10), req.body.fecha_corte, req.body.execution_key);
    
    res.send({ "message" : "Conciliacion iniciada", "error" : null });
};

