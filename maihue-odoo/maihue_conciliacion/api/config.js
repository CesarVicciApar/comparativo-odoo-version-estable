const cuenta_redondeo = {
    'account_id': 964,
    'reconcile_model_id': 23
};
const diarios = {
    "transdata": 12,
    "toku": 54,
    "multibanco_santander": 13,
    "santander": 11
};

const queryPaginatedLimit = 500;

const database_dev = {
    HOST: "127.0.0.1",
    USER: "odoo",
    PASSWORD: "odoo123*//",
    DB: "maihue_produccion",
    dialect: "postgres",
    pool: {
        max: 100,
        min: 0,
        acquire: 30000,
        idle: 10000
    }
};

const database_prod = {
    HOST: "odoo-master.ca1ccl1rflil.us-east-1.rds.amazonaws.com",
    USER: "postgres",
    PASSWORD: "icQxsj1edAY1wh97XvDw",
    DB: "maihue_production",
    dialect: "postgres",
    pool: {
        max: 100,
        min: 0,
        acquire: 30000,
        idle: 10000
    }
};

const database_seed = {
    HOST: "ec2-44-202-6-110.compute-1.amazonaws.com",
    USER: "odoo_api",
    PASSWORD: "odoo123*//",
    DB: "maihue_seed",
    dialect: "postgres",
    pool: {
        max: 100,
        min: 0,
        acquire: 30000,
        idle: 10000
    }
};


const database_release = {
    HOST: "odoo-release.ca1ccl1rflil.us-east-1.rds.amazonaws.com",
    USER: "postgres",
    PASSWORD: "54zaholgXCuOwPkSzjlP",
    DB: "maihue_release",
    dialect: "postgres",
    pool: {
        max: 100,
        min: 0,
        acquire: 30000,
        idle: 10000
    }
};

const odoo_local = {
    odoouser: "admin@blueminds.cl",
    odoopass: "Lata5rata",
    odooUrl: "http://localhost:8069",
    odoodb: "maihue_produccion"
}

const odoo_prod = {
    odoouser: "admin@blueminds.cl",
    odoopass: "Lata5rata",
    odooUrl: "https://odoo-production.maihuechile.cl",
    odoodb: "maihue_production"
}

const odoo_seed = {
    odoouser: "admin@blueminds.cl",
    odoopass: "Lata5rata",
    odooUrl: "http://ec2-44-202-6-110.compute-1.amazonaws.com:8069/",
    odoodb: "maihue_seed"
}


const odoo_release = {
    odoouser: "admin@blueminds.cl",
    odoopass: "Lata5rata",
    odooUrl: "https://odoo-release.maihuechile.cl",
    odoodb: "maihue_release"
}


module.exports = {
    cuenta_redondeo: cuenta_redondeo,
    diarios: diarios,
    getDatabase: () => {
        if (process.argv.slice(2).indexOf("--loc") >= 0) {
            return database_dev;
        }
        else if (process.argv.slice(2).indexOf("--dev") >= 0) {
            return database_dev;
        } else if (process.argv.slice(2).indexOf("--seed") >= 0) {
            return database_seed;
        } else if (process.argv.slice(2).indexOf("--prod") >= 0) {
            return database_prod;
        } else if (process.argv.slice(2).indexOf("--rel") >= 0) {
            return database_release;
        } else {
            return database_dev;
        }
    },
    getDatabaseWithform: (servidor) => {
        if (servidor !== null && servidor != undefined) {
            if (servidor.indexOf("loc") >= 0) {
                return database_dev;
            }
            else if (servidor.indexOf("dev") >= 0) {
                return database_dev;
            } else if (servidor.indexOf("seed") >= 0) {
                return database_seed;
            } else if (servidor.indexOf("prod") >= 0) {
                return database_prod;
            } else if (servidor.indexOf("release") >= 0) {
                return database_release;
            } else {
                return database_dev;
            }
        }

    },
    getOdooConnection: () => {
        if (process.argv.slice(2).indexOf("--loc") >= 0) {
            return odoo_local;
        }
        else if (process.argv.slice(2).indexOf("--dev") >= 0) {
            return odoo_local;
        } else if (process.argv.slice(2).indexOf("--seed") >= 0) {
            return odoo_seed;
        } else if (process.argv.slice(2).indexOf("--prod") >= 0) {
            return odoo_prod;
        } else if (process.argv.slice(2).indexOf("--rel") >= 0) {
            return odoo_release;
        } else {
            return odoo_local;
        }
    },
    getOdooConnectionWithForm: (servidor) => {
        if (servidor !== null && servidor != undefined) {
            if (servidor.indexOf("loc") >= 0) {
                return odoo_local;
            }
            else if (servidor.indexOf("dev") >= 0) {
                return odoo_local;
            } else if (servidor.indexOf("seed") >= 0) {
                return odoo_seed;
            } else if (servidor.indexOf("prod") >= 0) {
                return odoo_prod;
            } else if (servidor.indexOf("release") >= 0) {
                return odoo_release;
            } else {
                return odoo_local;
            }
        }
    },
    getValidJournals: () => {
        let keys = Object.keys(diarios);
        let result = [];
        for (let k of keys) {
            result.push(diarios[k]);
        }
        return result;
    },
    queryPaginatedLimit: queryPaginatedLimit
}