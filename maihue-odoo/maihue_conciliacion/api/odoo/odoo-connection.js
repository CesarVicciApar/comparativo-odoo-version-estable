const axios = require("axios");
let config = ""
let odoouser = ""
let odoopass = ""
let odooUrl = ""
let odoodb = ""

if (process.env.standalone) {
    config = require("../config").getOdooConnection();
    odoouser = config.odoouser;
    odoopass = config.odoopass;
    odooUrl = config.odooUrl;
    odoodb = config.odoodb;
}

//console.log(odoouser, odoopass, odooUrl, odoodb);

//console.log(configs);

async function authenticate() {
    const resp = await axios.post(`${odooUrl}/web/session/authenticate`, { "jsonrpc": "2.0", "params": { "db": odoodb, "login": odoouser, "password": odoopass } });

    const headers = {
        'content-type': 'application/json',
        'Cookie': resp.headers["set-cookie"][0]
    }

    return headers;

}
async function authenticate_withform(user, pass, server) {

    config = require("../config").getOdooConnectionWithForm(server);
    odoouser = config.odoouser;
    odoopass = config.odoopass;
    odooUrl = config.odooUrl;
    odoodb = config.odoodb;

    const resp = await axios.post(`${odooUrl}/web/session/authenticate`, { "jsonrpc": "2.0", "params": { "db": odoodb, "login": user, "password": pass } });
    console.log(resp);
    if (resp.data && resp.data.error) {
        return { error: "Usuario no autorizado" };
    } else {
        const headers = {
            'content-type': 'application/json',
            'Cookie': resp.headers["set-cookie"][0]
        }
        return headers;
    }
}
async function getReconciliation(headers, records) {

    try {


        const respo2 = await axios.post(`${odooUrl}/reconcile`, { "jsonrpc": "2.0", "params": records }, { headers: headers });

        if (respo2.data && respo2.data.result && respo2.data.result.result) {
            console.log(respo2.data);
            return respo2.data.result.result;
        } else {
            return "error";
        }




    }
    catch (ex) {
        console.error(ex.message);
    }


}


module.exports = {
    authenticate: authenticate,
    getReconciliation: getReconciliation,
    authenticate_withform: authenticate_withform
}