const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electron", {
  login: (data) => ipcRenderer.send("user:login", data),
  getConciliaciones: async () => {
    const conciliaciones = await ipcRenderer.invoke("conciliaciones:get");
    return conciliaciones;
  },
  recargar: async (time) => {
    const recargar = await ipcRenderer.invoke("conciliacion:recargar", time);
    return recargar;
  },
  conciliar_diario: async (time, journal, fc) => {
    const conciliar_diario = await ipcRenderer.invoke("conciliar:iniciar",  { journal : journal, fecha_corte : fc, time : time });
    return conciliar_diario;
  },
  });

ipcRenderer.on("login-failed", (event, message) => {
  document.getElementById("error-message").innerHTML = message;
  document.getElementById("cover-spin").style.display = "none";
});

ipcRenderer.on("reload-conciliacion", (event, message) => {
  document.getElementById("error-message").innerHTML = message;
  document.getElementById("cover-spin").style.display = "none";
});