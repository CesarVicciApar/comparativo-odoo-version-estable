let dbConfig;
const { QueryTypes } = require('sequelize');
const Sequelize = require("sequelize");
let connection;

if (process.env.standalone) {
  dbConfig = require("../config").getDatabase();
  console.log("DBCO===>", dbConfig.HOST);
  connection = new Sequelize(dbConfig.DB, dbConfig.USER, dbConfig.PASSWORD, {
    host: dbConfig.HOST,
    dialect: dbConfig.dialect,


    pool: {
      max: dbConfig.pool.max,
      min: dbConfig.pool.min,
      acquire: dbConfig.pool.acquire,
      idle: dbConfig.pool.idle
    }
  });

}


function initConnection(servidor) {
  dbConfig = require("../config").getDatabaseWithform(servidor);
  console.log("DBCO===>", dbConfig.HOST);
  connection =  new Sequelize(dbConfig.DB, dbConfig.USER, dbConfig.PASSWORD, {
    host: dbConfig.HOST,
    dialect: dbConfig.dialect,


    pool: {
      max: dbConfig.pool.max,
      min: dbConfig.pool.min,
      acquire: dbConfig.pool.acquire,
      idle: dbConfig.pool.idle
    }
  });
}

const db = {};

db.Sequelize = Sequelize;
db.connection = connection;
db.selectQuery = async (query, params, servidor = null) => {
  if (connection == null || connection == undefined) {
    initConnection(servidor);
    db.connection = connection;
  }
  
  const response = await db.connection.query(query, { type: QueryTypes.SELECT, replacements: params });
  return response;
};

db.updateQuery = async (query, params, servidor = null) => {
  if (connection == null || connection == undefined) {
    initConnection(servidor);
    db.connection = connection;
  }
  const response = await db.connection.query(query, { type: QueryTypes.UPDATE, replacements: params });
  return response;
}

db.insertQuery = async (query, params, servidor = null) => {
  if (connection == null || connection == undefined) {
    initConnection(servidor);
    db.connection = connection;
  }
  const response = await db.connection.query(query, { type: QueryTypes.INSERT, replacements: params });
  return response;
}


module.exports = db;