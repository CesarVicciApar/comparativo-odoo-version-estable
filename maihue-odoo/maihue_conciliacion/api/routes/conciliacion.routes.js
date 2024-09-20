module.exports = app => {
    const conciliacion = require("../controllers/conciliacion.controller");
  
    var router = require("express").Router();
  
    // Create a new Tutorial
    router.post("/", conciliacion.runConciliacion);
  
    
    app.use('/api/conciliacion', router);
  };