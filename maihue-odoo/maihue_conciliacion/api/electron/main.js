const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const path = require("path");
const api = require("../server");
const odoo = require("../odoo/odoo-connection");
const db = require("../database/db");
const axios = require("axios");
const { v4: uuidv4 } = require('uuid');

try {
   require('electron-reloader')(module)
} catch (_) { }
let mainWindow;
let user;
let execution_key = uuidv4();
let servidor = null; 
ipcMain.on("user:login", async (event, data) => {
   try {
      let headers = await odoo.authenticate_withform(data.username, data.password, data.servidor);

      if (headers.error) {
         event.reply("login-failed", headers.error);
      }
      else {
         user = data.username;
         servidor = data.servidor;
         openHome();
      }

   } catch (ex) {
      event.reply("login-failed", `Hubo un error al conectarse a odoo ${ex.message}`);

   }
});
ipcMain.handle("conciliacion:recargar", async (event, data) => {
   return data;
});
ipcMain.handle("conciliar:iniciar", async (event, data) => {
   const url = `http://127.0.0.1:${process.env.PORT || 8081}`;
   const resp = await axios.post(`${url}/api/conciliacion`, { "diario": data.journal, "fecha_corte": data.fecha_corte, execution_key: execution_key });

   console.log("RESP==>", resp);

   if (resp.data && resp.data.message == "Conciliacion iniciada") {

      return data.time;

   } else {
      event.reply("reload-conciliacion", `Hubo un error al iniciar conciliacion`);
   }

});

function createWindow() {

   mainWindow = new BrowserWindow({
      width: 1024,
      height: 768,
      minHeight: 768,
      minWidth: 1024,
      webPreferences: {
         preload: path.join(__dirname, "preload.js"),
      },

   });

   mainWindow.loadFile("./electron/index.html");

   mainWindow.on('close', async e => {
      e.preventDefault()
      try{
         const conciliaciones = await db.selectQuery(`SELECT 1 FROM l10n_cl_helpit_conciliacion_proceso WHERE execution_key = ? AND state in ('in_process', 'in_queue')`, [execution_key],servidor);
         if(conciliaciones.length){
            const { response } = await dialog.showMessageBox(mainWindow, {
               type: 'question',
               title: '  Advertencia  ',
               message: 'Hay procesos de conciliación ejecutándose actualmente, si cierra la ventana la operación quedará inconclusa y se tendrá que volver a ejecutar ¿Desea cerrar de todos modos?',
               buttons: ['Si', 'No']
            })
         
            response === 0 && mainWindow.destroy();
         }else{
            mainWindow.destroy()
         }  
      }catch{
         mainWindow.destroy()
      }
      
      
   });

   api.runApi();

}
ipcMain.handle("conciliaciones:get", async (event) => {

   const conciliaciones = await db.selectQuery(`SELECT cp.id, cp.journal,aj.name, cp.state, cp.date, cp.date_end, cp.fecha_corte
   FROM l10n_cl_helpit_conciliacion_proceso cp
    INNER join account_journal aj ON 
        aj.id = cp.journal
   `, null, servidor);

   return conciliaciones;
});

ipcMain.on("user:logout", (event) => {
   user = null;
   openIndex();
});

function openHome() {
   mainWindow.loadFile("./electron/home.html");
}
function openIndex() {
   mainWindow.loadFile("./electron/index.html");

}

app.whenReady().then(createWindow);
