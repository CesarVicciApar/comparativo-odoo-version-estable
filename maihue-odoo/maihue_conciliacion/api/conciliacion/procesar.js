const db = require("../database/db");
const tolerancia = 2;
const fs = require("node:fs");
const saveFile = false;
const odoo = require("../odoo/odoo-connection.js");
const config = require("../config.js");

//TOKU  39- o 33-
//PACK MULTIBANCO SANTANDER FAC o BEL
//TRANSDATA 


async function getAndByDiario(diario) {
	let retorno = "";
	switch (diario) {

		case config.diarios.santander:
			retorno = `AND(
	
			(
			 (CHAR_LENGTH(payment_ref) - CHAR_LENGTH(REPLACE(payment_ref, '.', ''))) 	/ CHAR_LENGTH('.') > 2
			 AND 
			 (CHAR_LENGTH(payment_ref) - CHAR_LENGTH(REPLACE(payment_ref, '-', ''))) / CHAR_LENGTH('-') = 1
		
		  )
			
			OR 
			
			(
			  payment_ref ~ '\\d{10}'
			)
			
		
		)`;
			break;
		case config.diarios.multibanco_santander:
		case config.diarios.toku:
		case config.diarios.transdata:
			retorno = `	AND ( position('C3C' in payment_ref)= 0
			AND  position('NCuotas' in payment_ref) = 0)
			AND ( position('-33-' in payment_ref) > 0
			OR  position('-39-' in payment_ref) > 0
			OR  position('39-' in payment_ref) > 0
			OR  position('33-' in payment_ref) > 0
			OR position(' BEL ' in payment_ref) > 0
			OR position(' FAC ' in payment_ref) > 0)`;
			break;

	}

	return retorno;

}

async function comenzar(diario, fecha_corte, ultima_cantidad) {



	const lineas = await obtenerLineas(diario, fecha_corte, (await getAndByDiario(diario)));
	const querys = getQuerys(lineas, diario);
	const boletas = querys.queryBoletas ? await db.selectQuery(querys.queryBoletas) : null;
	const facturas = querys.queryFacturas ? await db.selectQuery(querys.queryFacturas) : null;
	const anyDoc = querys.queryAny ? await db.selectQuery(querys.queryAny) : null;


	const resultadoBoletas = boletas ? await parearResultados(boletas, querys.busquedasBoletas, "T39", diario) : [];
	const resultadoFacturas = facturas ? await parearResultados(facturas, querys.busquedasFacturas, "T33", diario) : [];
	const resultadoAny = anyDoc ? await parearResultados(anyDoc, querys.busquedasAny, "ANY", diario) : [];


	if (resultadoBoletas.length && saveFile) {
		saveFiles(resultadoBoletas, "boletas.csv")

	}

	if (resultadoFacturas.length && saveFile) {
		saveFiles(resultadoFacturas, "facturas.csv")
	}
	if (resultadoAny.length && saveFile) {
		saveFiles(resultadoAny, "any.csv")
	}


	if (!saveFile) {

		if (resultadoFacturas.length || resultadoBoletas.length || resultadoAny.length) {

			let cantidad_actual = (resultadoBoletas.length ? resultadoBoletas.length : 0) + (resultadoFacturas.length ? resultadoFacturas.length : 0) + (resultadoAny.length ? resultadoAny.length : 0)
			console.log("Cantidad actual==>", cantidad_actual, ultima_cantidad);
			await send(resultadoFacturas, resultadoBoletas, resultadoAny);


			if (ultima_cantidad != cantidad_actual) {
				console.log("ESPERANDO 10 Segundos a que termine todo para continuar");
				await new Promise(r => setTimeout(r, 10000));
				await comenzar(diario, fecha_corte, cantidad_actual);
			}


		}

	}


}

async function send(resultadoFacturas, resultadoBoletas, resultadoAny) {
	const headers = await odoo.authenticate();

	if (resultadoFacturas.length) {
		await sendData(headers, resultadoFacturas);
	}

	if (resultadoBoletas.length) {
		await sendData(headers, resultadoBoletas);
	}

	if (resultadoAny.length) {
		await sendData(headers, resultadoAny);
	}
}

async function procesar(diario, fecha_corte, execution_key) {
	const procesos = await db.selectQuery("SELECT journal, state FROM l10n_cl_helpit_conciliacion_proceso WHERE state = 'in_process'");

	if (procesos.length == 0) {
		await db.updateQuery("UPDATE l10n_cl_helpit_conciliacion_proceso SET state = 'in_process', date = NOW(), date_end = null, execution_key = ? WHERE journal = ?", [execution_key, diario]);
		await comenzar(diario, fecha_corte, null);

		await db.updateQuery("UPDATE l10n_cl_helpit_conciliacion_proceso SET state = 'no_executed', date_end = NOW(), execution_key = ? WHERE journal = ? and state = 'in_process'", ["", diario]);
		const procesos = await db.selectQuery("SELECT journal, state, fecha_corte FROM l10n_cl_helpit_conciliacion_proceso WHERE state = 'in_queue' LIMIT 1");
		console.log("AQUI SE CAE=>", procesos);
		if (procesos.length > 0) {

			await procesar(procesos[0]["journal"], procesos[0]["fecha_corte"], execution_key);
		}


	} else {
		await db.updateQuery("UPDATE l10n_cl_helpit_conciliacion_proceso SET state = 'in_queue', date = null, date_end = null, execution_key = ? WHERE journal = ?", [execution_key, diario]);
	}
}


async function sendData(headers, resultado) {

	let line = [];
	let data = [];
	let xx = 0;
	let x = 0;
	let promises = [];
	let sended = 0;
	console.log("ENVIANDO", resultado.length);
	let records = {
		"records": []
	};

	for (let b of resultado) {
		//console.log(b["movimientos"].length == 1, b["movimientos"][0][0], parseInt(b["monto"]), parseInt(b["movimientos"][0][0]["amount_move_total"]), parseInt(b["monto"]) == parseInt(b["movimientos"][0][0]["amount_move_total"]))
		if (b["movimientos"].length == 1 && b["movimientos"][0].length == 1) {
			//if (b["movimientos"].length == 1 && b["movimientos"][0].length == 1) {



			let lines_vals_list = [{

				"name": b["movimientos"][0][0]["name"],
				"balance": parseInt(b["movimientos"][0][0]["balance"] * -1),
				"analytic_tag_ids": [[6, null, []]],
				"id": parseInt(b["movimientos"][0][0]["line_id"]),
				"currency_id": parseInt(b["movimientos"][0][0]["currency_id"])
			}];


			if ((parseInt(b["monto"]) > parseInt(b["movimientos"][0][0]["amount_move_total"])) || (parseInt(b["monto"]) < parseInt(b["movimientos"][0][0]["amount_move_total"]))) {

				let monto = parseInt(b["movimientos"][0][0]["amount_move_total"]) - parseInt(b["monto"]);

				lines_vals_list.push(
					{ 'name': b["nombre_linea"], 'balance': monto, 'analytic_tag_ids': [[6, false, []]], 'account_id': config.cuenta_redondeo.account_id, 'reconcile_model_id': config.cuenta_redondeo.reconcile_model_id, 'currency_id': parseInt(b["movimientos"][0][0]["currency_id"]) }
				)
			}

			line.push(parseInt(b["id_statement"]));
			data.push(
				{
					"partner_id": parseInt(b["movimientos"][0][0]["partner_id_move"]),
					"lines_vals_list": lines_vals_list,
					"to_check": false
				}

			);

			records.records.push({
				"lines": line,
				"data": data
			});

			sended += 1;
			if (records.records.length == 20) {
				promises.push(odoo.getReconciliation(headers, records));
				x += 1;
				records.records = [];
			}



			if ((x % 1) == 0) {
				process.stdout.write(`                                         ENVIANDOOOOOOOOOOOOOOOO=> ${sended} \r`);
				await Promise.all(promises);
				promises = [];
				x = 0;
			}


		}
		line = [];
		data = [];

	}

	if (records.records.length > 0) {
		promises.push(odoo.getReconciliation(headers, records));
		console.log("ULTIMAS");
		process.stdout.write(`                                         ENVIANDOOOOOOOOOOOOOOOO=> ${promises.length} \r`);
		await Promise.all(promises);
	}

}

function saveFiles(resultados, name) {
	let file = "id_statement;nombre_linea;monto;numero;partner;name;date;journal_id;partner_id_move;amount_move_total;move_id;move_line_id;balance;currency\n";

	for (let b of resultados) {
		for (let l of b["movimientos"]) {
			for (let m of l) {
				file += `${b['id_statement']};${b['nombre_linea']};${b['monto']};${b['numero']};${b['partner']};${m['name']};${m['date']};${m['journal_id']};${m['partner_id_move']};${m['amount_move_total']};${m['move_id']};${m['line_id']};${m["balance"] * -1};${m["currency_id"]}\n`;
			}
		}
	}
	fs.writeFile(name, file, err => {
		if (err) {
			console.error(err);
		}
	});
}

function searchCoincidence(b, cursor, bolfac, diario) {

	return new Promise((resolve, rejects) => {
		let currentResultado = null;

		switch (diario) {
			case config.diarios.multibanco_santander:
			case config.diarios.toku:
			case config.diarios.transdata:
				currentResultado = cursor.filter((c) => {
					return parseInt(c["amount_move_total"]) >= b["tolerancia_abajo"] &&
						parseInt(c["amount_move_total"]) <= b["tolerancia_arriba"] &&
						c["name"].indexOf(b["numero"]) >= 0 &&
						b["bolfac"] == bolfac;
				});
				break;
			case config.diarios.santander:
				currentResultado = cursor.filter((c) => {
					return parseInt(c["amount_move_total"]) == b["monto"] && c["vat"] == b["rut"];
				});
		}

		b["movimientos"].push(currentResultado);
		resolve(true);

	});

}

async function parearResultados(cursor, busquedas, bolfac, diario) {


	let x = 0
	console.log("PAREANDO", cursor.length, busquedas.length);
	let promises = [];
	let xx = 0;
	console.time("x100");
	for (let b of busquedas) {

		promises.push(searchCoincidence(b, cursor, bolfac, diario));


		x += 1;

		if ((x % 1000) == 0) {
			await Promise.all(promises);
			promises = [];
			x = 0;
		}
		xx += 1;
		process.stdout.write(xx + "\r");


	}

	if (promises.length > 0) {
		await Promise.all(promises);
	}

	console.timeEnd("x100");
	return busquedas

}

function formatRut(rut, withDots = false) {
	// XX.XXX.XXX-X
	const newRut = rut.replace(/\./g, '').replace(/\-/g, '').trim().toLowerCase();
	const lastDigit = newRut.substr(-1, 1);
	const rutDigit = newRut.substr(0, newRut.length - 1)
	let format = '';
	for (let i = rutDigit.length; i > 0; i--) {
		const e = rutDigit.charAt(i - 1);
		format = e.concat(format);

		if (i % 3 === 0 && withDots) {
			format = '.'.concat(format);
		}
	}
	return format.concat('-').concat(lastDigit);
}

function getBusqueda(id, ref, amount, partner_id, diario) {

	try {
		partner_id = partner_id ? partner_id : 1;
		tolerancia_arriba = parseInt(amount) + tolerancia;
		tolerancia_abajo = parseInt(amount) - tolerancia;
		if (diario == config.diarios.transdata) {
			if (ref.indexOf("-33-") >= 0) {
				bolfac = ref.substring(ref.indexOf("-33-"));
				bolfac = bolfac.split(" ")[0].split("-");
			}
			else if (ref.indexOf("-39-") >= 0) {
				bolfac = ref.substring(ref.indexOf("-39-"));
				bolfac = bolfac.split(" ")[0].split("-");
			}
			else if (ref.indexOf("BEL") >= 0) {
				bolfac = ref.substring(ref.indexOf(" BEL "));
				bolfac = bolfac.split(" ");
			}
			else if (ref.indexOf("FAC") >= 0) {
				bolfac = ref.substring(ref.indexOf(" FAC "));
				bolfac = bolfac.split(" ");
			}
			return {
				"id_statement": id,
				"bolfac": bolfac[1] == '39' || bolfac[1] == "BEL" ? "T39" : (bolfac[1] == '33' || bolfac[1] == "FAC" ? "T33" : null),
				"nombre_linea": ref,
				"tolerancia_abajo": tolerancia_abajo,
				"monto": parseInt(amount),
				"tolerancia_arriba": tolerancia_arriba,
				"numero": bolfac[2],
				"partner": partner_id,
				"movimientos": []
			}
		} else if (diario == config.diarios.toku) {

			if (ref.indexOf("33-") >= 0) {
				bolfac = ref.substring(ref.indexOf("33-"));
				bolfac = bolfac.split(" ")[0].split("-");
			}
			else if (ref.indexOf("39-") >= 0) {
				bolfac = ref.substring(ref.indexOf("39-"));
				bolfac = bolfac.split(" ")[0].split("-");
			}
			return {
				"id_statement": id,
				"bolfac": bolfac[0] == '39' ? "T39" : (bolfac[0] == '33' ? "T33" : null),
				"nombre_linea": ref,
				"tolerancia_abajo": tolerancia_abajo,
				"monto": parseInt(amount),
				"tolerancia_arriba": tolerancia_arriba,
				"numero": bolfac[1],
				"partner": partner_id,
				"movimientos": []
			}

		} else if (diario == config.diarios.multibanco_santander) {

			if (ref.indexOf("BEL") >= 0) {
				bolfac = ref.substring(ref.indexOf(" BEL "));
				bolfac = bolfac.split(" ");
			}
			else if (ref.indexOf("FAC") >= 0) {
				bolfac = ref.substring(ref.indexOf(" FAC "));
				bolfac = bolfac.split(" ");
			}

			return {
				"id_statement": id,
				"bolfac": bolfac[1] == "BEL" ? "T39" : (bolfac[1] == "FAC" ? "T33" : null),
				"nombre_linea": ref,
				"tolerancia_abajo": tolerancia_abajo,
				"monto": parseInt(amount),
				"tolerancia_arriba": tolerancia_arriba,
				"numero": bolfac[2],
				"partner": partner_id,
				"movimientos": []
			}
		} else if (diario == config.diarios.santander) {


			const regex = /\d{10}/g;
			const regex2 = /\b\d{2}\.\d{3}\.\d{3}\-\d\b/g;

			const match = ref.match(regex);
			const match2 = ref.match(regex2);
			let rut = null;

			if (match && match[0]) {
				rut = formatRut(parseInt(match[0], 10).toString());
			} else if (match2 && match2[0]) {
				rut = formatRut(match2[0]);
			} else {
				return null;
			}

			return {
				"id_statement": id,
				"bolfac": "ANY",
				"nombre_linea": ref,
				"tolerancia_abajo": tolerancia_abajo,
				"monto": parseInt(amount),
				"tolerancia_arriba": tolerancia_arriba,
				"numero": "",
				"rut": rut,
				"partner": partner_id,
				"movimientos": []
			}
		}

	}
	catch {
		return null;
	}



}

function getBaseQuery(diario, tipo) {

	switch (diario) {

		case config.diarios.santander:
			return "select c.vat, a.currency_id, b.id as line_id, b.name as line_name, b.balance as balance,  a.name, a.date, a.journal_id, a.partner_id as partner_id_move, a.amount_total as amount_move_total , a.id as move_id from account_move a, account_move_line b, res_partner c where a.payment_state = 'not_paid' and a.state = 'posted'  AND a.id = b.move_id and b.full_reconcile_id IS NULL and a.partner_id = c.id  and a.name = b.name and ( "
		case config.diarios.multibanco_santander:
		case config.diarios.toku:
		case config.diarios.transdata:
			if (tipo == "f") {
				return "select a.currency_id, b.id as line_id, b.name as line_name, b.balance  as balance,  a.name, a.date, a.journal_id, a.partner_id as partner_id_move, a.amount_total as amount_move_total , a.id as move_id from account_move a, account_move_line b where a.payment_state = 'not_paid' and a.state = 'posted' and position('T33' in a.id_factura) > 0 AND a.id = b.move_id AND a.name = b.name and b.full_reconcile_id IS NULL AND a.id_factura IN (";
			} else if (tipo == "b") {
				return "select a.currency_id, b.id as line_id, b.name as line_name, b.balance as balance,  a.name, a.date, a.journal_id, a.partner_id as partner_id_move, a.amount_total as amount_move_total , a.id as move_id from account_move a, account_move_line b where a.payment_state = 'not_paid' and a.state = 'posted' and position('T39' in a.id_factura) > 0 AND a.id = b.move_id AND a.name = b.name and b.full_reconcile_id IS NULL AND a.id_factura IN ("
			}
			break;
		default:
			return null;
	}

}

async function executeQueryPaginated(query, params, limit, offset, retorno = []) {


	let q = `${query} LIMIT ${limit} OFFSET ${offset};` ;
	console.log("EJECUCION", q, params, limit, offset);
	
	let queryResult = await db.selectQuery(q, params);
	if (queryResult && queryResult.length > 0) {
		retorno = retorno.concat(queryResult);
		return await executeQueryPaginated(query, params, limit, offset += limit, retorno);
	} else {
		return retorno;
	}

}

function getQuerys(lineas, diario) {

	let queryBoletas = getBaseQuery(diario, "b");
	console.log("BOL=>", queryBoletas);
	let queryFacturas = getBaseQuery(diario, "f");
	console.log("FAC=>", queryFacturas);
	let queryAny = getBaseQuery(diario, null);
	console.log("ANY=>", queryAny);

	let busquedasBoletas = [];
	let busquedasFacturas = [];
	let busquedasAny = [];
	let hasBoletas = false;
	let hasFacturas = false;
	let hasAny = false;
	for (let linea of lineas) {


		let busqueda = getBusqueda(linea.id, linea.payment_ref, linea.amount, linea.partner_id, diario);
		if (busqueda === null || busqueda.bolfac === null) {
			continue;
		}
		if (busqueda["bolfac"] == "ANY" && busqueda["rut"] && busqueda["monto"]) {
			hasAny = true;
			busquedasAny.push(busqueda);
			queryAny += `(c.vat = '${busqueda["rut"]}' and a.amount_total = ${busqueda["monto"]}) OR `;

		} else if (busqueda["bolfac"] == "T39") {
			hasBoletas = true;
			busquedasBoletas.push(busqueda)
			queryBoletas += `'T39F${busqueda["numero"]}',`;
		} else {
			hasFacturas = true;
			busquedasFacturas.push(busqueda)
			queryFacturas += `'T33F${busqueda["numero"]}',`;
		}

	}

	queryBoletas = queryBoletas && queryBoletas != null ? queryBoletas.slice(0, -1) + ");" : null;
	queryFacturas = queryFacturas && queryFacturas != null ? queryFacturas.slice(0, -1) + ");" : null;
	queryAny = queryAny && queryAny != null ? queryAny.slice(0, -3) + ");" : null;

	return {
		"queryBoletas": hasBoletas ? queryBoletas : null,
		"queryFacturas": hasFacturas ? queryFacturas : null,
		"queryAny": hasAny ? queryAny : null,
		"busquedasBoletas": busquedasBoletas,
		"busquedasFacturas": busquedasFacturas,
		"busquedasAny": busquedasAny
	}

}

/*

AND(
	
	(
	 (CHAR_LENGTH(payment_ref) - CHAR_LENGTH(REPLACE(payment_ref, '.', ''))) 	/ CHAR_LENGTH('.') > 2
	 AND 
	 (CHAR_LENGTH(payment_ref) - CHAR_LENGTH(REPLACE(payment_ref, '-', ''))) / CHAR_LENGTH('-') = 1

  )
	
	OR 
	
	(
	  payment_ref ~ '\d{10}'
	)
	

)
*/


/*
	AND ( position('C3C' in payment_ref)= 0
	AND  position('NCuotas' in payment_ref) = 0)
	AND ( position('-33-' in payment_ref) > 0
	OR  position('-39-' in payment_ref) > 0
	OR  position('39-' in payment_ref) > 0
	OR  position('33-' in payment_ref) > 0
	OR position(' BEL ' in payment_ref) > 0
	OR position(' FAC ' in payment_ref) > 0)


*/

async function obtenerLineas(diario, fecha_corte, and) {

	const query = `SELECT
	"account_bank_statement_line".id,
    "account_bank_statement_line".payment_ref,
    "account_bank_statement_line".amount,
    "account_bank_statement_line".partner_id
     
FROM
	"account_bank_statement_line"
	LEFT JOIN "account_move" AS "account_bank_statement_line__move_id" ON ( "account_bank_statement_line"."move_id" = "account_bank_statement_line__move_id"."id" )
	LEFT JOIN "account_bank_statement" AS "account_bank_statement_line__statement_id" ON ( "account_bank_statement_line"."statement_id" = "account_bank_statement_line__statement_id"."id" ) 
WHERE
	(
		(
			(
				( ( "account_bank_statement_line__move_id"."journal_id" IN ( :diario ) ) OR "account_bank_statement_line__move_id"."journal_id" IS NULL ) 
				AND (
					"account_bank_statement_line"."statement_id" IN (
					SELECT
						"account_bank_statement".ID 
					FROM
						"account_bank_statement" 
					WHERE
						( "account_bank_statement"."state" = 'posted' ) 
						AND ( "account_bank_statement"."company_id" IS NULL OR ( "account_bank_statement"."company_id" IN ( 1 ) ) ) 
					) 
				) 
			) 
			AND ( "account_bank_statement_line"."is_reconciled" IS NULL OR "account_bank_statement_line"."is_reconciled" = FALSE ) 
		) 
		AND ( "account_bank_statement_line__move_id"."date" > :fecha_corte ) 
	) 
	AND ( "account_bank_statement_line__move_id"."company_id" IS NULL OR ( "account_bank_statement_line__move_id"."company_id" IN ( 1 ) ) ) 
	AND ( "account_bank_statement_line__move_id"."company_id" IS NULL OR ( "account_bank_statement_line__move_id"."company_id" IN ( 1 ) ) ) 
    ${and}
ORDER BY
	"account_bank_statement_line__statement_id"."date" ASC,
	"account_bank_statement_line__statement_id"."name" ASC,
	"account_bank_statement_line__statement_id"."id" ASC,
	"account_bank_statement_line__move_id"."date",
	"account_bank_statement_line"."sequence",
	"account_bank_statement_line"."id" DESC`;

	const lineas = await executeQueryPaginated(query, { diario: diario, fecha_corte: fecha_corte }, config.queryPaginatedLimit, 0, []);

	return lineas;

}

module.exports = {

	procesar: procesar

}