from odoo import api, fields, models, _
from odoo.exceptions import UserError
import requests
import json
import logging
from datetime import timedelta, date, datetime, tzinfo
import base64
import xmltodict
from xml.dom import minidom

_logger = logging.getLogger(__name__)

URL_DICOM_COMMERCIAL = {
    'qa': 'https://uapi.equifax.cl/efc-informe-empresarial-rest/',
    'prod': 'https://api.equifax.cl/efc-informe-empresarial-rest/',
}

URL_DICOM_PLATINUM = {
    'qa': 'https://uws.equifax.cl/osb-efx/equifax/Platinum360PassengerV2?wsdl',
    'prod': 'https://ws.equifax.cl/osb-efx/equifax/Platinum360PassengerV2?wsdl'
}

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _default_status_partner_dicom(self):
        return self.env.company.status

    def _default_status_dicom_active(self):
        return self.env.company.dicom_active

    # def compute_dicom_active(self):
    #     company = self.env.company
    #     for record in self:
    #         record.dicom_active = company.dicom_active

    dicom_active = fields.Boolean(default=_default_status_dicom_active, track_visibility="onchange")
    status = fields.Selection(string='STATUS', selection=[('qa_local', 'QA'), ('qa', 'Testing'), ('prod', 'Produccion')], default=_default_status_partner_dicom, track_visibility="onchange")
    history_dicom_id = fields.Many2one('history.request.dicom', string='Historial', track_visibility="onchange")
    dicom_report_ids = fields.One2many('dicom.report', 'partner_id', track_visibility="onchange")
    dicom_last_score = fields.Integer(string="Score Dicom", track_visibility="onchange")
    dicom_last_date = fields.Date(string="Last Date", track_visibility="onchange")
    service_type = fields.Selection(string='Informe',
                                    selection=[('commercial', 'Empresarial'), ('platinum', 'Platinum360')], track_visibility="onchange")
    status_dicom = fields.Selection(string='Estado Dicom',
                                    selection=[('approved', 'Aprobado'), ('rejected', 'Rechazado'),
                                               ('check', 'Revisar'), ('to_check', 'Por Consultar'), ('error', 'Error')],
                                    default='to_check', track_visibility="onchange")
    dicom_value_test = fields.Integer('Prueba', help='Ingresar un numero entre 0-999 para test de dicom')
    status_exception_dicom = fields.Selection(string='Estado Excepcion Dicom',
                                              selection=[('not_exception', 'Sin excepcion'),
                                                         ('exception', 'Excepcion Activa'),
                                                         ('exception_due', 'Excepcion Vencida')],
                                              default='not_exception', track_visibility="onchange")
    date_today = fields.Date(string='Fecha hoy', compute='_compute_date_today')
    date_today_test = fields.Date(string='Fecha hoy')
    dicom_exception = fields.Boolean(string='Excepcion Dicom')
    dicom_exception_date = fields.Date(string="Dicom Exception Date", track_visibility="onchange")

    def _compute_date_today(self):
        for record in self:
            record.date_today = datetime.now().date()

    def empresarial(self):
        return '''{"data":
            {
                "commercialData":{
                    "behavior":{
                        "contactability":{
                            "contactsDataDetail":{
                                "addresses":{
                                    "commercialAddresses":
                                        [
                                            {
                                                "addressDate":"20120131",
                                                "addressType":"COMERCIAL",
                                                "addressUpdateDate":"20130219",
                                                "aditionalInfo":null,
                                                "city":"SANTIAGO",
                                                "codeRegion":"RM",
                                                "communes":"RECOLETA",
                                                "lastAddressVerificationDate":null,
                                                "number":"386",
                                                "postalCode":"8420494",
                                                "region":"METROPOLITANA DE SANTIAGO",
                                                "sourceOfAddress":"COMERCIAL  - DIRECCIONES SIN VERIFICAR",
                                                "street":"Mitchell Isle",
                                                "streetAndNumber":"Mitchell Isle 386 "
                                            },{
                                                "addressDate":"20000430",
                                                "addressType":"COMERCIAL",
                                                "addressUpdateDate":"20040105",
                                                "aditionalInfo":null,
                                                "city":"SANTIAGO",
                                                "codeRegion":"RM",
                                                "communes":"NUNOA",
                                                "lastAddressVerificationDate":null,
                                                "number":"47966",
                                                "postalCode":"7770391",
                                                "region":"METROPOLITANA DE SANTIAGO",
                                                "sourceOfAddress":"FISCAL     - REG PROVENIENTES DEL DIRECTORIO DE EMPRESAS FUENTE JUR",
                                                "street":"Pouros Junction",
                                                "streetAndNumber":"Pouros Junction 47966 "
                                            }
                                        ]
                                },
                                "emails":{"referenceData":[]},
                                "telephones":{
                                    "referenceData":
                                        [
                                            {
                                                "codCountry":null,
                                                "codInoSource":null,
                                                "codeArea":"02",
                                                "descInfoSource":null,
                                                "isPrivate":"",
                                                "lastUpdate":"19900101",
                                                "numCountry":"56",
                                                "referencyCode":"TF",
                                                "referencyDesc":"22237970",
                                                "referencyDescSubType":null,
                                                "referencyTypeCode":"TF",
                                                "referencyTypeDesc":"PHONE",
                                                "validationDate":"19900101"
                                            },{
                                                "codCountry":null,
                                                "codInoSource":null,
                                                "codeArea":"02",
                                                "descInfoSource":null,
                                                "isPrivate":"",
                                                "lastUpdate":"19900101",
                                                "numCountry":"56",
                                                "referencyCode":"TF",
                                                "referencyDesc":"27350376",
                                                "referencyDescSubType":null,
                                                "referencyTypeCode":"TF",
                                                "referencyTypeDesc":"PHONE",
                                                "validationDate":"19900101"
                                            }
                                        ]
                                },
                                "verificationAddresses":{
                                    "addressVerifData":[]
                                },
                                "websites":{
                                    "referenceData":[]
                                }
                            },
                            "contactsDataSummary":{
                                "addressCount":0,
                                "dateLastAddress":"",
                                "emailLastDate":"",
                                "lastEmail":"",
                                "lastTelephone":"0222237970",
                                "lastWebsite":"",
                                "telephoneLastDate":"19900101",
                                "totalEmail":"0",
                                "totalTelephone":"2",
                                "totalWebsite":"0",
                                "websiteLastDate":""
                            }
                        },
                        "identification":{
                            "bankruptcy":{
                                "bankruptcyResume":[]
                            },
                            "identificationCompany":{
                                "activities":{
                                    "activities":[]
                                },
                                "activity":null,
                                "actualAddress":null,
                                "bankruptciesQuantity":"0",
                                "businessName":"SOC DE TRANSPORTES ARAYA Y BRAY LIMITADA",
                                "email":null,
                                "fantasyName":"RODRIGO ARAYA Y CIA LTDA",
                                "initDate":"19991104",
                                "rut":"0773550905",
                                "warrantyQuantity":"1",
                                "webSite":null
                            }
                        }
                    },
                    "capacity":{
                        "historical":{
                            "commercialHistorical":[]
                        },
                        "verifications":{
                            "workVerifData":[]
                        }
                    },
                    "credit":{
                        "bank":{
                            "banksActive":{
                                "commercialBanksActive":[]
                            },
                            "closedCurrentAcount":{
                                "commercialClosedCurrentAcount":[]
                            },
                            "numberOfBlockedAccounts":1,
                            "totalBank":"0",
                            "unableToOpenAccountIndicator":null
                        },
                        "boletinConcursal":{
                            "detailBoletinConcursal":{
                                "commercialDetailBoletinConcursal":[]
                            },
                            "summaryBolConcursal":{
                                "flagBoletinConcursal":null,
                                "publicationNumberBolConcursal":null
                            }
                        },
                        "consultRut":{
                            "detailConsultRut":{
                                "commercialDetailConsultRUT":[]
                            },
                            "inquiriesNumber":"0",
                            "timelapseNumber":20,
                            "timelapseTypeUsed":"MESES"
                        },
                        "creditRisk":{
                            "everclean":null,
                            "evercleanDateUpdate":null,
                            "historicalRate":{
                                "commercialHistoricalRate":[]
                            },
                            "historicalRatingReport":"N",
                            "importantAspect":{
                                "commercialImportantAspect":[]
                            },
                            "originOfUse":"PREDEMPR",
                            "personsRate":"%s",
                            "predictorScale":{
                                "maximumRate":"0",
                                "minimumRate":"0",
                                "percentageOfConsumers":0,
                                "typeOfRisk":"",
                                "unpaymentProbability":0
                            },
                            "lessPercentage":null
                        },
                        "debtsSummary":{
                            "accessCamaraComercio":"SI",
                            "amountAccumulated6Months":0,
                            "bed":{
                                "commercialBed":[{
                                    "chequeOperatioNumber":"320","debtType":"Morosidad","documentType":"FA","equifaxRegisterDate":"20200807","expirationDate":"20200309","justificationDate":"20200807","justificationDescription":null,"libradorName":"EQUIFAX CHILE","localidadName":null,"marketCode":"09","marketDescription":"SERVICIOS DE EMPRESAS","moneyCode":"$","typeReason":null,"unpaidAmount":"723520","visibilityDate":"20200807"
                                }]
                            },
                            "bolab":{
                                "commercialBolab":[]
                            },
                            "bolcom":{
                                "commercialBolcom":[{
                                    "boletinNumber":"4813",
                                    "boletinPage":"314",
                                    "chequeOperatioNumber":"0",
                                    "creditType":null,
                                    "debtType":"Protesto",
                                    "documentType":"PG",
                                    "expirationDate":"20210426",
                                    "justificationDate":null,
                                    "justificationDescription":"Protesto",
                                    "libradorName":"HOSPITAL HERNAN HENRIQUEZ ARAVENA DE TCO.                   ","localidadName":"TEMUCO","marketCode":"99","marketDescription":"NO CLASIFICADOS","moneyCode":"$","notarioName":"HECTOR BASUALTO BUST","reasonType":"FP","registerDate":"","unpaidAmount":"256210"
                                },{
                                    "boletinNumber":"4813",
                                    "boletinPage":"314",
                                    "chequeOperatioNumber":"0",
                                    "creditType":null,
                                    "debtType":"Protesto",
                                    "documentType":"PG",
                                    "expirationDate":"20210426",
                                    "justificationDate":null,
                                    "justificationDescription":"Protesto",
                                    "libradorName":"HOSPITAL HERNAN HENRIQUEZ ARAVENA DE TCO.                   ","localidadName":"TEMUCO","marketCode":"99","marketDescription":"NO CLASIFICADOS","moneyCode":"$","notarioName":"HECTOR BASUALTO BUST","reasonType":"FP","registerDate":"","unpaidAmount":"155450"
                                }]
                            },
                            "conectionAicssErrorIndicator":"N",
                            "debtsSummaryDetail":{
                                "amountLastDebts":null,
                                "dateLastDebts":null,
                                "totalAmountDebts":"1135180",
                                "totalDebts":3
                            },
                            "delinquencyNumber":1,
                            "docsAmountAccumulated12Months":"0",
                            "docsAmountAccumulated24Months":"0",
                            "docsAmountAccumulated6Months":"0",
                            "docsAmountAccumulatedMoreThan24Months":"1135",
                            "docsAmountFrom12To24Months":"0",
                            "docsAmountFrom6To12Months":"0",
                            "docsAmountLast6Months":"0",
                            "docsAmountMoreThan24Months":"1135",
                            "icom":{
                                "commercialIcom":[]
                            },
                            "infoSectionIndicator":"SI",
                            "lastDateBoletinLaboral":"",
                            "market":{
                                "commercialMarket":[{
                                    "marketCode":"09",
                                    "marketDescription":"SERVICIOS DE EMPRESAS",
                                    "unpaidAmount":"723520",
                                    "unpaidNumber":1
                                },{
                                    "marketCode":"99",
                                    "marketDescription":"NO CLASIFICADOS",
                                    "unpaidAmount":"411660",
                                    "unpaidNumber":2
                                }]
                            },
                            "protestSummary":{
                                "amountLastProtest":null,
                                "expirationDateLastProtest":null,
                                "totalAmountProtests":"411.66",
                                "totalProtests":0
                            },
                            "summaryBolab":{
                                "amountLastBolab":null,
                                "expirationDateLastBolab":null,
                                "totalAmountBolab":"0",
                                "totalBolab":0
                            },
                            "summaryBolcom":{
                                "summaryAmountLast":"256210",
                                "summaryExpirationDateLast":"20210426",
                                "summaryTotal":2,
                                "summaryTotalAmount":"411660"
                            },
                            "summaryBed":{
                                "summaryAmountLast":"723520",
                                "summaryExpirationDateLast":"20200309",
                                "summaryTotal":1,
                                "summaryTotalAmount":"723520"
                            },
                            "summaryIcom":{
                                "summaryAmountLast":null,
                                "summaryExpirationDateLast":null,
                                "summaryTotal":0,
                                "summaryTotalAmount":"0"
                            },
                            "totalDocsAccumulated12Months":0,
                            "totalDocsAccumulated24Months":0,
                            "totalDocsAccumulatedMoreThan24Months":3,
                            "totalDocsBoletinProtestosEImpagos":3,
                            "totalDocsFrom12To24Months":0,
                            "totalDocsFrom6To12Months":0,
                            "totalDocsIcom":0,
                            "totalDocsLast6Months":0,
                            "totalDocsMoreThan24Months":3,
                            "totalMultaeInfraccionLaboralPrevisional":0,
                            "unpaidAmountPesos":"1135180",
                            "unpaidAmountThousandPesos":1135,
                            "unpaidLastAmount":"256210",
                            "unpaidLastDebtType":"PROTESTO",
                            "unpaidLastExpirationDate":"20210426",
                            "unpaidNumberInformed":3,
                            "unpaidProtestDebtsThousandPesos":"1135",
                            "unpaidTotalAmount":"1135",
                            "unpaidTotalNumber":"3"
                        },
                        "detailImpedido":{
                            "impedido":[]
                        },
                        "justification":{
                            "commercialJustification":[]
                        },
                        "onp":{
                            "detailOnp":{
                                "commercialDetailOnp":[]
                            },
                            "summaryOnp":{
                                "onpLastMonths":0,
                                "onpMonthsNumber":12,
                                "onpNumber":0
                            }
                        },
                        "sbif":{
                            "sbifDetail":{
                                "commercialSbifDetail":[]
                            },
                            "sbifSummary":{
                                "detailsCount":"0",
                                "latestFinancialDebt":null,
                                "presenceOfDetails":"N",
                                "totalDebts":null
                            }
                        }
                    },
                    "guarantees":{
                        "accreditations":{
                            "accreditationsFlag":"SI",
                            "commercialPartnerPartnership":{
                                "activities":{
                                    "activityData":[]
                                },
                                "commercialCompanyData":{
                                    "commercialCompanyEmpresarial":[]
                                },
                                "commercialPartners":{
                                    "commercialPartnerEmpresarial":[]
                                },
                                "executives":{
                                    "executiveData":[]
                                },
                                "mallaCommercialCompanyData":{
                                    "mallaCompanyEmpresarial":[]
                                },
                                "mallaCommercialPartners":{
                                    "mallaPartnerEmpresarial":[]
                                },
                                "sizeSection":{
                                    "approximateVehiclesValue":"0",
                                    "dimensionDate":"20121231",
                                    "dimensionIndicatorCode":"1",
                                    "dimensionIndicatorDesc":null,
                                    "lastPeriodTurnover":"1",
                                    "numberOfEmployees":"1",
                                    "numberOfProperties":"0",
                                    "numberOfVehicles":"5",
                                    "totalPropertiesValue":"0"
                                },
                                "taxDeclaration":{
                                    "dateOldTaxDeclaration":"2004-04-30T00:00:00.000+00:00",
                                    "dateTaxDeclaration":null,
                                    "pageOldTaxDeclaration":"00000008554",
                                    "pageTaxDeclaration":null,
                                    "typeOldTaxDeclaration":"O",
                                    "typeTaxDeclaration":null
                                }
                            },
                            "externalTrade":{
                                "financialIndicators":{
                                    "fechaDolar":"20230622",
                                    "fechaUF":"20230622",
                                    "fechaUTM":"20230622",
                                    "valorDolar":"",
                                    "valorUF":"",
                                    "valorUTM":"61157"
                                },
                                "lastAmountExport":null,
                                "lastAmountImport":"5969",
                                "lastYearExport":"00010101",
                                "lastyearImport":"20131201"
                            },
                            "gse":{
                                "gseCode":"S",
                                "gseDate":null,
                                "gseSource":null
                            },
                            "obbligations":{
                                "obbligation":[]
                            },
                            "personPartnerPartnership":{
                                "countRelationshipsPartner":null,
                                "countRelationshipsSociety":null,
                                "personPartnership":{
                                    "mallaCompanyEmpresarial":[]
                                },
                                "societies":{
                                    "societies":[]
                                }
                            },
                            "proprieties":{
                                "proprietiesData":[]
                            },
                            "realEstate":{
                                "propertiesCount":"0",
                                "totalAssesmentAmountPesos":"0"
                            },
                            "sii":{
                                "categorySII":null,
                                "dateUpdateInfoInicioAct":null,
                                "dateUpdateInfoUltimoTimbraje":null,
                                "detailEconomicActivity":{
                                    "economicActivityTemp":[]
                                },
                                "economicActivityCode":null,
                                "economicActivityDescription":null,
                                "inicioActividades":null,
                                "lastTaxPeriod":null,
                                "lastTaxPeriodNumber":null,
                                "observacionesTributarias":{
                                    "commercialTaxViolationComments":[]
                                },
                                "observacionesTributariasNumber":0,
                                "rubro":null,
                                "startSIIDate":null,
                                "taxInfraction":{
                                    "taxViolationData":[]
                                },
                                "ultimoTimbraje":null
                            },
                            "vehicles":{
                                "carActualizationDate":"20210226",
                                "carTaxValuation":null,
                                "comercialValuationCar":null,
                                "detailCars":{
                                    "detailCar":[{
                                        "flagActualOwner":"V",
                                        "flagHistoryAvailable":"S",
                                        "vehicleStructure":{
                                            "carSerial":null,
                                            "carValue":"0",
                                            "chasisSerial":"RZH112-0026746",
                                            "classificationType":{
                                                "code":"L",
                                                "description":"LIVIANO"
                                            },
                                            "color":{
                                                "code":"0007",
                                                "description":"AMARILLO"
                                            },
                                            "colorOther":null,
                                            "dateLastCRAcquisition":"2021-02-26T00:00:00.000+00:00",
                                            "dateLastTransfeFROM":"2009-01-13T00:00:00.000+00:00",
                                            "dateLastTransfer":"2009-01-13T00:00:00.000+00:00",
                                            "dateLastTransferTO":null,
                                            "dateLastUpdate":"2014-03-19T00:00:00.000+00:00",
                                            "dateStartValidity":"2014-03-19T00:00:00.000+00:00",
                                            "fuelDescription":"N/A",
                                            "mark":{
                                                "code":"2629",
                                                "description":"TOYOTA"
                                            },
                                            "model":{
                                                "code":"049638",
                                                "description":"HI ACE 2.0"
                                            },
                                            "motorSerial":"1RZ-0558913",
                                            "plate":"LH2374",
                                            "plateCheck":"2",
                                            "type":{
                                                "code":"0016",
                                                "description":"FURGON"
                                            },
                                            "yearManufacture":"1994"
                                        }
                                    },{
                                        "flagActualOwner":"V",
                                        "flagHistoryAvailable":"S",
                                        "vehicleStructure":{
                                            "carSerial":null,
                                            "carValue":"0",
                                            "chasisSerial":"9BM3840734B375376",
                                            "classificationType":{
                                                "code":"P",
                                                "description":"PESADO"
                                            },"color":{
                                                "code":"0011",
                                                "description":"GRIS"
                                            },
                                            "colorOther":null,
                                            "dateLastCRAcquisition":"2021-02-26T00:00:00.000+00:00",
                                            "dateLastTransfeFROM":"2009-12-18T00:00:00.000+00:00",
                                            "dateLastTransfer":"2009-12-18T00:00:00.000+00:00",
                                            "dateLastTransferTO":null,
                                            "dateLastUpdate":"2011-12-27T00:00:00.000+00:00",
                                            "dateStartValidity":"2011-12-27T00:00:00.000+00:00",
                                            "fuelDescription":"N/A",
                                            "mark":{
                                                "code":"1813",
                                                "description":"MERCEDES BENZ"
                                            },
                                            "model":{
                                                "code":"032659",
                                                "description":"OF 1721 59"
                                            },
                                            "motorSerial":"37797310593446",
                                            "plate":"YP9153",
                                            "plateCheck":"4",
                                            "type":{
                                                "code":"0003",
                                                "description":"BUS"
                                            },
                                            "yearManufacture":"2005"
                                        }
                                    },{
                                        "flagActualOwner":"V",
                                        "flagHistoryAvailable":"S",
                                        "vehicleStructure":{"carSerial":null,"carValue":"0","chasisSerial":"9BM6882761B279479","classificationType":{"code":"P","description":"PESADO"},"color":{"code":"0004","description":"GIALLINO"},"colorOther":"VERDE","dateLastCRAcquisition":"2021-02-26T00:00:00.000+00:00","dateLastTransfeFROM":"2008-06-27T00:00:00.000+00:00","dateLastTransfer":"2008-06-27T00:00:00.000+00:00","dateLastTransferTO":null,"dateLastUpdate":"2011-12-27T00:00:00.000+00:00","dateStartValidity":"2011-12-27T00:00:00.000+00:00","fuelDescription":"N/A","mark":{"code":"1813","description":"MERCEDES BENZ"},"model":{"code":"032447","description":"LO 914"},"motorSerial":"904924508978","plate":"VC6877","plateCheck":"2","type":{"code":"0003","description":"BUS"},"yearManufacture":"2002"}
                                    },{
                                        "flagActualOwner":"V","flagHistoryAvailable":"N","vehicleStructure":{"carSerial":null,"carValue":"0","chasisSerial":"9BM384073YB224950","classificationType":{"code":"P","description":"PESADO"},"color":{"code":"0004","description":"GIALLINO"},"colorOther":"ROJO AZUL","dateLastCRAcquisition":"2021-02-26T00:00:00.000+00:00","dateLastTransfeFROM":"2007-05-30T00:00:00.000+00:00","dateLastTransfer":"2007-05-30T00:00:00.000+00:00","dateLastTransferTO":null,"dateLastUpdate":"2011-12-23T00:00:00.000+00:00","dateStartValidity":"2011-12-23T00:00:00.000+00:00","fuelDescription":"N/A","mark":{"code":"1813","description":"MERCEDES BENZ"},"model":{"code":"032884","description":"OF 1721"},"motorSerial":"37797310459514","plate":"UH2955","plateCheck":"7","type":{"code":"0003","description":"BUS"},"yearManufacture":"2001"}
                                    },{
                                        "flagActualOwner":"V","flagHistoryAvailable":"N","vehicleStructure":{"carSerial":null,"carValue":"0","chasisSerial":null,"classificationType":{"code":"P","description":"PESADO"},"color":{"code":"0004","description":"GIALLINO"},"colorOther":null,"dateLastCRAcquisition":"2021-02-26T00:00:00.000+00:00","dateLastTransfeFROM":"2000-03-06T00:00:00.000+00:00","dateLastTransfer":"2000-03-06T00:00:00.000+00:00","dateLastTransferTO":null,"dateLastUpdate":"2011-12-23T00:00:00.000+00:00","dateStartValidity":"2011-12-23T00:00:00.000+00:00","fuelDescription":"N/A","mark":{"code":"0847","description":"IVECO"},"model":{"code":"016174","description":"59.12"},"motorSerial":"2127753","plate":"RS4457","plateCheck":"2","type":{"code":"0014","description":"CHASSIS"},"yearManufacture":"1998"}
                                    }]
                                },
                                "detailOwners":{
                                    "detailOwner":[]
                                },
                                "resumeCar":{
                                    "dateLastCRAcquisition":null,
                                    "flagActualOwner":null,
                                    "presenceOfDetails":null,
                                    "totalNumberOwners":null,
                                    "vehicleStructure":{
                                        "carSerial":null,
                                        "carValue":null,
                                        "chasisSerial":null,
                                        "classificationType":{
                                            "code":null,
                                            "description":null
                                        },
                                        "color":{
                                            "code":null,
                                            "description":null
                                        },
                                        "colorOther":null,
                                        "dateLastCRAcquisition":null,
                                        "dateLastTransfeFROM":null,
                                        "dateLastTransfer":null,
                                        "dateLastTransferTO":null,
                                        "dateLastUpdate":null,
                                        "dateStartValidity":null,
                                        "fuelDescription":null,
                                        "mark":{
                                            "code":null,
                                            "description":null
                                        },
                                        "model":{
                                            "code":null,
                                            "description":null
                                        },
                                        "motorSerial":null,
                                        "plate":null,
                                        "plateCheck":null,
                                        "type":{
                                            "code":null,
                                            "description":null
                                        },
                                        "yearManufacture":null
                                    }
                                },
                                "resumeOwner":{
                                    "dateLastCRAcquisition":"2021-02-26T00:00:00.000+00:00",
                                    "flagHistorical":"N",
                                    "owner":{
                                        "fatherSurname":null,
                                        "motherSurname":null,
                                        "name":null,
                                        "rut":null,
                                        "tradeName":null,
                                        "typeId":null
                                    },
                                    "presenceOfDetails":"S",
                                    "totalAmountHeavyCars":"0",
                                    "totalAmountLightCars":"0",
                                    "totalAmountOtherCars":"0",
                                    "totalNumberCars":"5",
                                    "totalNumberHeavyCars":"4",
                                    "totalNumberLightCars":"1",
                                    "totalNumberOtherCars":"0"
                                },
                                "totalNumberCars":"5",
                                "totalNumberHeavyCars":"4",
                                "totalNumberLightCars":"1",
                                "totalNumberOtherCars":"0"
                            }
                        }
                    },
                    "lanzamientosData":{
                        "detailLanzamiento":{
                            "lanzamientosTemp":[]
                        },"summaryLanzamiento":{
                            "courtLastLanzamiento":null,
                            "dateLastLanzamiento":null,
                            "lastJudgmentCase":null,
                            "lastLanzamiento":null,
                            "roleLastLanzamient":null,
                            "totalLanzamientos":null
                        }
                    },
                    "transactionInfo":{
                        "transactionID":"01",
                        "transactionTime":null
                    }
                }
            }
        }''' % self.dicom_value_test

    def platinum(self):
        return '''<?xml version="1.0" encoding="UTF-8"?>
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
                <soapenv:Header/>
                <soapenv:Body>
                    <get:getInformePlatinum360Response xmlns:get="http://cl.equifax.com/schema/Platinum360/GetInformePlatinum360BResp">
                        <get:response>
                            <get:Credit>
                                <get:CreditRisk>
                                    <get:PersonsRate>{}.0</get:PersonsRate>
                                    <get:HistoricalRatingReport>N</get:HistoricalRatingReport>
                                    <get:OriginOfUse/>
                                    <get:Everclean/>
                                    <get:EvercleanDateUpdate>00010101</get:EvercleanDateUpdate>
                                    <get:HistoricalRate/>
                                    <get:PredictorScale>
                                        <get:TypeOfRisk/>
                                        <get:MinimumRate>0</get:MinimumRate>
                                        <get:MaximumRate>0</get:MaximumRate>
                                        <get:PercentageOfConsumers/><get:UnpaymentProbability/>
                                    </get:PredictorScale>
                                    <get:ImportantAspect/>
                                </get:CreditRisk>
                                <get:DebtsSummary>
                                    <get:LastDateBoletinLaboral/>
                                    <get:AccessCamaraComercio>SI</get:AccessCamaraComercio>
                                    <get:InfoSectionIndicator>SI</get:InfoSectionIndicator>
                                    <get:ConectionAICSSErrorIndicator>N</get:ConectionAICSSErrorIndicator>
                                    <get:UnpaidTotalNumber>15</get:UnpaidTotalNumber>
                                    <get:UnpaidTotalAmount>5120</get:UnpaidTotalAmount>
                                    <get:UnpaidLastExpirationDate>20220701</get:UnpaidLastExpirationDate>
                                    <get:UnpaidLastAmount>800000</get:UnpaidLastAmount>
                                    <get:UnpaidLastDebtType>MOROSIDAD</get:UnpaidLastDebtType>
                                    <get:DocsAmountLast6Months>0</get:DocsAmountLast6Months>
                                    <get:TotalDocsLast6Months>0</get:TotalDocsLast6Months>
                                    <get:AmountAccumulated6Months>0</get:AmountAccumulated6Months>
                                    <get:DocsAmountAccumulated6Months>0</get:DocsAmountAccumulated6Months>
                                    <get:DocsAmountFrom6To12Months>4499</get:DocsAmountFrom6To12Months>
                                    <get:TotalDocsFrom6To12Months>11</get:TotalDocsFrom6To12Months>
                                    <get:TotalDocsAccumulated12Months>11</get:TotalDocsAccumulated12Months>
                                    <get:DocsAmountAccumulated12Months>4499</get:DocsAmountAccumulated12Months>
                                    <get:DocsAmountFrom12To24Months>621</get:DocsAmountFrom12To24Months>
                                    <get:TotalDocsFrom12To24Months>4</get:TotalDocsFrom12To24Months>
                                    <get:TotalDocsAccumulated24Months>15</get:TotalDocsAccumulated24Months>
                                    <get:DocsAmountAccumulated24Months>5120</get:DocsAmountAccumulated24Months>
                                    <get:DocsAmountMoreThan24Months>0</get:DocsAmountMoreThan24Months>
                                    <get:TotalDocsMoreThan24Months>0</get:TotalDocsMoreThan24Months>
                                    <get:TotalDocsAccumulatedMoreThan24Months>0</get:TotalDocsAccumulatedMoreThan24Months>
                                    <get:DocsAmountAccumulatedMoreThan24Months>0</get:DocsAmountAccumulatedMoreThan24Months>
                                    <get:UnpaidNumberInformed>15</get:UnpaidNumberInformed>
                                    <get:DelinquencyNumber>15</get:DelinquencyNumber>
                                    <get:TotalDocsBoletinProtestosEImpagos>15</get:TotalDocsBoletinProtestosEImpagos>
                                    <get:TotalDocsICOM>0</get:TotalDocsICOM>
                                    <get:TotalMultaeInfraccionLaboralPrevisional>0</get:TotalMultaeInfraccionLaboralPrevisional>
                                    <get:UnpaidAmountPesos>5119859</get:UnpaidAmountPesos>
                                    <get:UnpaidProtestDebtsThousandPesos>5120</get:UnpaidProtestDebtsThousandPesos>
                                    <get:Market>
                                        <get:MarketType>
                                            <get:MarketCode>08</get:MarketCode>
                                            <get:MarketDescription>RETAIL</get:MarketDescription>
                                            <get:UnpaidNumber>15</get:UnpaidNumber>
                                            <get:UnpaidAmount>5119859.52</get:UnpaidAmount>
                                        </get:MarketType>
                                    </get:Market>
                                    <get:DebtsSummaryDetail>
                                        <get:TotalDebts>15</get:TotalDebts>
                                        <get:TotalAmountDebts>5119859</get:TotalAmountDebts>
                                        <get:DateLastDebts/><get:AmountLastDebts/>
                                    </get:DebtsSummaryDetail>
                                    <get:BED>
                                        <get:BEDType>
                                            <get:ExpirationDate>20220701</get:ExpirationDate>
                                            <get:DocumentType>PG</get:DocumentType>
                                            <get:MoneyCode>$</get:MoneyCode>
                                            <get:UnpaidAmount>800000</get:UnpaidAmount>
                                            <get:LibradorName>nOMBRE DEL APORTANTE</get:LibradorName>
                                            <get:LocalidadName/>
                                            <get:DebtType>Morosidad</get:DebtType>
                                            <get:ChequeOperatioNumber>QA123PG11</get:ChequeOperatioNumber>
                                            <get:EquifaxRegisterDate>20220809</get:EquifaxRegisterDate>
                                            <get:JustificationDescription/>
                                            <get:JustificationDate>20220809</get:JustificationDate>
                                            <get:MarketCode>08</get:MarketCode>
                                            <get:MarketDescription>RETAIL</get:MarketDescription>
                                            <get:TypeReason/>
                                            <get:VisibilityDate>20220809</get:VisibilityDate>
                                        </get:BEDType>
                                        <get:BEDType>
                                            <get:ExpirationDate>20220701</get:ExpirationDate>
                                            <get:DocumentType>PG</get:DocumentType>
                                            <get:MoneyCode>$</get:MoneyCode>
                                            <get:UnpaidAmount>8000</get:UnpaidAmount>
                                            <get:LibradorName>nOMBRE DEL APORTANTE</get:LibradorName>
                                            <get:LocalidadName/>
                                            <get:DebtType>Morosidad</get:DebtType>
                                            <get:ChequeOperatioNumber>12345312</get:ChequeOperatioNumber>
                                            <get:EquifaxRegisterDate>20220809</get:EquifaxRegisterDate>
                                            <get:JustificationDescription/>
                                            <get:JustificationDate>20220809</get:JustificationDate>
                                            <get:MarketCode>08</get:MarketCode>
                                            <get:MarketDescription>RETAIL</get:MarketDescription>
                                            <get:TypeReason/>
                                            <get:VisibilityDate>20220809</get:VisibilityDate>
                                        </get:BEDType>
                                        <get:BEDType>
                                            <get:ExpirationDate>20220701</get:ExpirationDate><get:DocumentType>PG</get:DocumentType><get:MoneyCode>$</get:MoneyCode><get:UnpaidAmount>500000</get:UnpaidAmount><get:LibradorName>nOMBRE DEL APORTANTE</get:LibradorName><get:LocalidadName/><get:DebtType>Morosidad</get:DebtType><get:ChequeOperatioNumber>123PruebaQAPG355</get:ChequeOperatioNumber><get:EquifaxRegisterDate>20220808</get:EquifaxRegisterDate><get:JustificationDescription/><get:JustificationDate>20220808</get:JustificationDate><get:MarketCode>08</get:MarketCode><get:MarketDescription>RETAIL</get:MarketDescription><get:TypeReason/><get:VisibilityDate>20220808</get:VisibilityDate>
                                        </get:BEDType>
                                        <get:BEDType>
                                            <get:ExpirationDate>20220701</get:ExpirationDate><get:DocumentType>PG</get:DocumentType><get:MoneyCode>$</get:MoneyCode><get:UnpaidAmount>100000</get:UnpaidAmount><get:LibradorName>nOMBRE DEL APORTANTE</get:LibradorName><get:LocalidadName/><get:DebtType>Morosidad</get:DebtType><get:ChequeOperatioNumber>PruebaQAPG3348</get:ChequeOperatioNumber><get:EquifaxRegisterDate>20220808</get:EquifaxRegisterDate><get:JustificationDescription/><get:JustificationDate>20220808</get:JustificationDate><get:MarketCode>08</get:MarketCode><get:MarketDescription>RETAIL</get:MarketDescription><get:TypeReason/><get:VisibilityDate>20220808</get:VisibilityDate>
                                        </get:BEDType>
                                        <get:BEDType>
                                            <get:ExpirationDate>20220701</get:ExpirationDate><get:DocumentType>PG</get:DocumentType><get:MoneyCode>$</get:MoneyCode><get:UnpaidAmount>500000</get:UnpaidAmount><get:LibradorName>nOMBRE DEL APORTANTE</get:LibradorName><get:LocalidadName/><get:DebtType>Morosidad</get:DebtType><get:ChequeOperatioNumber>PruebaQAPG3347</get:ChequeOperatioNumber><get:EquifaxRegisterDate>20220808</get:EquifaxRegisterDate><get:JustificationDescription/><get:JustificationDate>20220808</get:JustificationDate><get:MarketCode>08</get:MarketCode><get:MarketDescription>RETAIL</get:MarketDescription><get:TypeReason/><get:VisibilityDate>20220808</get:VisibilityDate>
                                        </get:BEDType>
                                        <get:BEDType>
                                            <get:ExpirationDate>20220701</get:ExpirationDate><get:DocumentType>PG</get:DocumentType><get:MoneyCode>$</get:MoneyCode><get:UnpaidAmount>800000</get:UnpaidAmount><get:LibradorName>nOMBRE DEL APORTANTE</get:LibradorName><get:LocalidadName/><get:DebtType>Morosidad</get:DebtType><get:ChequeOperatioNumber>QA123PG1</get:ChequeOperatioNumber><get:EquifaxRegisterDate>20220809</get:EquifaxRegisterDate><get:JustificationDescription/><get:JustificationDate>20220809</get:JustificationDate><get:MarketCode>08</get:MarketCode><get:MarketDescription>RETAIL</get:MarketDescription><get:TypeReason/><get:VisibilityDate>20220809</get:VisibilityDate>
                                        </get:BEDType>
                                        <get:BEDType>
                                            <get:ExpirationDate>20220701</get:ExpirationDate><get:DocumentType>BO</get:DocumentType><get:MoneyCode>$</get:MoneyCode><get:UnpaidAmount>800.24</get:UnpaidAmount><get:LibradorName>nOMBRE DEL APORTANTE</get:LibradorName><get:LocalidadName/><get:DebtType>Morosidad</get:DebtType><get:ChequeOperatioNumber>123PruebaQA</get:ChequeOperatioNumber><get:EquifaxRegisterDate>20220808</get:EquifaxRegisterDate><get:JustificationDescription/><get:JustificationDate>20220808</get:JustificationDate><get:MarketCode>08</get:MarketCode><get:MarketDescription>RETAIL</get:MarketDescription><get:TypeReason/><get:VisibilityDate>20220808</get:VisibilityDate>
                                        </get:BEDType>
                                        <get:BEDType>
                                            <get:ExpirationDate>20220701</get:ExpirationDate><get:DocumentType>BO</get:DocumentType><get:MoneyCode>UF</get:MoneyCode><get:UnpaidAmount>59.28</get:UnpaidAmount><get:LibradorName>nOMBRE DEL APORTANTE</get:LibradorName><get:LocalidadName/><get:DebtType>Morosidad</get:DebtType><get:ChequeOperatioNumber>123PruebaQA</get:ChequeOperatioNumber><get:EquifaxRegisterDate>20220808</get:EquifaxRegisterDate><get:JustificationDescription/><get:JustificationDate>20220808</get:JustificationDate><get:MarketCode>08</get:MarketCode><get:MarketDescription>RETAIL</get:MarketDescription><get:TypeReason/><get:VisibilityDate>20220808</get:VisibilityDate>
                                        </get:BEDType>
                                        <get:BEDType>
                                            <get:ExpirationDate>20220701</get:ExpirationDate><get:DocumentType>PG</get:DocumentType><get:MoneyCode>$</get:MoneyCode><get:UnpaidAmount>500000</get:UnpaidAmount><get:LibradorName>nOMBRE DEL APORTANTE</get:LibradorName><get:LocalidadName/><get:DebtType>Morosidad</get:DebtType><get:ChequeOperatioNumber>123PrbaQAPG3ASS3</get:ChequeOperatioNumber><get:EquifaxRegisterDate>20220808</get:EquifaxRegisterDate><get:JustificationDescription/><get:JustificationDate>20220808</get:JustificationDate><get:MarketCode>08</get:MarketCode><get:MarketDescription>RETAIL</get:MarketDescription><get:TypeReason/><get:VisibilityDate>20220808</get:VisibilityDate>
                                        </get:BEDType>
                                        <get:BEDType>
                                            <get:ExpirationDate>20220701</get:ExpirationDate><get:DocumentType>PG</get:DocumentType><get:MoneyCode>$</get:MoneyCode><get:UnpaidAmount>790000</get:UnpaidAmount><get:LibradorName>nOMBRE DEL APORTANTE</get:LibradorName><get:LocalidadName/><get:DebtType>Morosidad</get:DebtType><get:ChequeOperatioNumber>12345312</get:ChequeOperatioNumber><get:EquifaxRegisterDate>20220809</get:EquifaxRegisterDate><get:JustificationDescription/><get:JustificationDate>20220809</get:JustificationDate><get:MarketCode>08</get:MarketCode><get:MarketDescription>RETAIL</get:MarketDescription><get:TypeReason/><get:VisibilityDate>20220809</get:VisibilityDate>
                                        </get:BEDType>
                                        <get:BEDType>
                                            <get:ExpirationDate>20220701</get:ExpirationDate><get:DocumentType>PG</get:DocumentType><get:MoneyCode>$</get:MoneyCode><get:UnpaidAmount>500000</get:UnpaidAmount><get:LibradorName>nOMBRE DEL APORTANTE</get:LibradorName><get:LocalidadName/><get:DebtType>Morosidad</get:DebtType><get:ChequeOperatioNumber>123PruebaQAPG334</get:ChequeOperatioNumber><get:EquifaxRegisterDate>20220808</get:EquifaxRegisterDate><get:JustificationDescription/><get:JustificationDate>20220808</get:JustificationDate><get:MarketCode>08</get:MarketCode><get:MarketDescription>RETAIL</get:MarketDescription><get:TypeReason/><get:VisibilityDate>20220808</get:VisibilityDate>
                                        </get:BEDType>
                                        <get:BEDType>
                                            <get:ExpirationDate>20211201</get:ExpirationDate><get:DocumentType>PG</get:DocumentType><get:MoneyCode>$</get:MoneyCode><get:UnpaidAmount>49000</get:UnpaidAmount><get:LibradorName>nOMBRE DEL APORTANTE</get:LibradorName><get:LocalidadName/><get:DebtType>Morosidad</get:DebtType><get:ChequeOperatioNumber>PRUEBAQA</get:ChequeOperatioNumber><get:EquifaxRegisterDate>20211223</get:EquifaxRegisterDate><get:JustificationDescription/><get:JustificationDate>20211223</get:JustificationDate><get:MarketCode>08</get:MarketCode><get:MarketDescription>RETAIL</get:MarketDescription><get:TypeReason/><get:VisibilityDate>20211223</get:VisibilityDate>
                                        </get:BEDType>
                                        <get:BEDType>
                                            <get:ExpirationDate>20211201</get:ExpirationDate><get:DocumentType>PG</get:DocumentType><get:MoneyCode>$</get:MoneyCode><get:UnpaidAmount>500000</get:UnpaidAmount><get:LibradorName>nOMBRE DEL APORTANTE</get:LibradorName><get:LocalidadName/><get:DebtType>Morosidad</get:DebtType><get:ChequeOperatioNumber>QA12334</get:ChequeOperatioNumber><get:EquifaxRegisterDate>20220120</get:EquifaxRegisterDate><get:JustificationDescription/><get:JustificationDate>20220120</get:JustificationDate><get:MarketCode>08</get:MarketCode><get:MarketDescription>RETAIL</get:MarketDescription><get:TypeReason/><get:VisibilityDate>20220120</get:VisibilityDate>
                                        </get:BEDType>
                                        <get:BEDType>
                                            <get:ExpirationDate>20211101</get:ExpirationDate><get:DocumentType>PG</get:DocumentType><get:MoneyCode>$</get:MoneyCode><get:UnpaidAmount>2000</get:UnpaidAmount><get:LibradorName>nOMBRE DEL APORTANTE</get:LibradorName><get:LocalidadName/><get:DebtType>Morosidad</get:DebtType><get:ChequeOperatioNumber>123QA</get:ChequeOperatioNumber><get:EquifaxRegisterDate>20211202</get:EquifaxRegisterDate><get:JustificationDescription/><get:JustificationDate>20211202</get:JustificationDate><get:MarketCode>08</get:MarketCode><get:MarketDescription>RETAIL</get:MarketDescription><get:TypeReason/><get:VisibilityDate>20211202</get:VisibilityDate>
                                        </get:BEDType>
                                        <get:BEDType>
                                            <get:ExpirationDate>20211101</get:ExpirationDate><get:DocumentType>PG</get:DocumentType><get:MoneyCode>$</get:MoneyCode><get:UnpaidAmount>70000</get:UnpaidAmount><get:LibradorName>nOMBRE DEL APORTANTE</get:LibradorName><get:LocalidadName/><get:DebtType>Morosidad</get:DebtType><get:ChequeOperatioNumber>PG123QA</get:ChequeOperatioNumber><get:EquifaxRegisterDate>20211202</get:EquifaxRegisterDate><get:JustificationDescription/><get:JustificationDate>20211202</get:JustificationDate><get:MarketCode>08</get:MarketCode><get:MarketDescription>RETAIL</get:MarketDescription><get:TypeReason/><get:VisibilityDate>20211202</get:VisibilityDate>
                                        </get:BEDType>
                                    </get:BED>
                                    <get:ICOM/>
                                    <get:ProtestSummary>
                                        <get:TotalProtests>0</get:TotalProtests>
                                        <get:TotalAmountProtests>5120</get:TotalAmountProtests>
                                        <get:ExpirationDateLastProtest/><get:AmountLastProtest/>
                                    </get:ProtestSummary>
                                    <get:BOLCOM/>
                                    <get:SumaryBOLAB>
                                        <get:TotalBolab>0</get:TotalBolab>
                                        <get:TotalAmountBolab>0</get:TotalAmountBolab>
                                        <get:ExpirationDateLastBolab/><get:AmountLastBolab/>
                                    </get:SumaryBOLAB>
                                    <get:BOLAB/>
                                </get:DebtsSummary>
                                <get:Bank>
                                    <get:UnableToOpenAccountIndicator>N</get:UnableToOpenAccountIndicator>
                                    <get:NumberOfBlockedAccounts>1</get:NumberOfBlockedAccounts>
                                    <get:TotalBank>0</get:TotalBank>
                                    <get:BanksActive/>
                                    <get:ClosedCurrentAcount/>
                                </get:Bank>
                                <get:Onp>
                                    <get:SumaryONP>
                                        <get:OnpNumber>0</get:OnpNumber>
                                        <get:OnpLastMonths>0</get:OnpLastMonths>
                                        <get:OnpMonthsNumber>3</get:OnpMonthsNumber>
                                    </get:SumaryONP>
                                    <get:DetailONP/>
                                </get:Onp>
                                <get:ConsultRUT>
                                    <get:TimelapseNumber>6</get:TimelapseNumber>
                                    <get:TimelapseTypeUsed>MESES</get:TimelapseTypeUsed>
                                    <get:InquiriesNumber>12</get:InquiriesNumber>
                                    <get:DetailConsultRUT>
                                        <get:DetailConsultRUTType>
                                            <get:InquiryDate>20230623</get:InquiryDate>
                                            <get:InquiryCompanyName>BDEBUENO SPA</get:InquiryCompanyName>
                                            <get:InquiryReportName>PLATINUM360</get:InquiryReportName>
                                        </get:DetailConsultRUTType>
                                        <get:DetailConsultRUTType>
                                            <get:InquiryDate>20230619</get:InquiryDate>
                                            <get:InquiryCompanyName>BDEBUENO SPA</get:InquiryCompanyName>
                                            <get:InquiryReportName>PLATINUM360</get:InquiryReportName>
                                        </get:DetailConsultRUTType>
                                        <get:DetailConsultRUTType>
                                            <get:InquiryDate>20230619</get:InquiryDate><get:InquiryCompanyName>BDEBUENO SPA</get:InquiryCompanyName><get:InquiryReportName>PLATINUM360</get:InquiryReportName>
                                        </get:DetailConsultRUTType>
                                        <get:DetailConsultRUTType>
                                            <get:InquiryDate>20230619</get:InquiryDate><get:InquiryCompanyName>BDEBUENO SPA</get:InquiryCompanyName><get:InquiryReportName>PLATINUM360</get:InquiryReportName>
                                        </get:DetailConsultRUTType>
                                        <get:DetailConsultRUTType>
                                            <get:InquiryDate>20230619</get:InquiryDate><get:InquiryCompanyName>BDEBUENO SPA</get:InquiryCompanyName><get:InquiryReportName>PLATINUM360</get:InquiryReportName>
                                        </get:DetailConsultRUTType>
                                        <get:DetailConsultRUTType>
                                            <get:InquiryDate>20230619</get:InquiryDate><get:InquiryCompanyName>BDEBUENO SPA</get:InquiryCompanyName><get:InquiryReportName>PLATINUM360</get:InquiryReportName>
                                        </get:DetailConsultRUTType>
                                        <get:DetailConsultRUTType>
                                            <get:InquiryDate>20230619</get:InquiryDate><get:InquiryCompanyName>BDEBUENO SPA</get:InquiryCompanyName><get:InquiryReportName>PLATINUM360</get:InquiryReportName>
                                        </get:DetailConsultRUTType>
                                        <get:DetailConsultRUTType>
                                            <get:InquiryDate>20230619</get:InquiryDate><get:InquiryCompanyName>BDEBUENO SPA</get:InquiryCompanyName><get:InquiryReportName>PLATINUM360</get:InquiryReportName>
                                        </get:DetailConsultRUTType>
                                        <get:DetailConsultRUTType>
                                            <get:InquiryDate>20230619</get:InquiryDate><get:InquiryCompanyName>BDEBUENO SPA</get:InquiryCompanyName><get:InquiryReportName>PLATINUM360</get:InquiryReportName>
                                        </get:DetailConsultRUTType>
                                        <get:DetailConsultRUTType>
                                            <get:InquiryDate>20230619</get:InquiryDate><get:InquiryCompanyName>BDEBUENO SPA</get:InquiryCompanyName><get:InquiryReportName>PLATINUM360</get:InquiryReportName>
                                        </get:DetailConsultRUTType><get:DetailConsultRUTType><get:InquiryDate>20230619</get:InquiryDate><get:InquiryCompanyName>BDEBUENO SPA</get:InquiryCompanyName><get:InquiryReportName>PLATINUM360</get:InquiryReportName></get:DetailConsultRUTType><get:DetailConsultRUTType><get:InquiryDate>20230619</get:InquiryDate><get:InquiryCompanyName>BDEBUENO SPA</get:InquiryCompanyName><get:InquiryReportName>PLATINUM360</get:InquiryReportName></get:DetailConsultRUTType>
                                    </get:DetailConsultRUT>
                                </get:ConsultRUT>
                                <get:BoletinConcursal>
                                    <get:SumaryBolConcursal/>
                                    <get:DetailBoletinConcursal/>
                                </get:BoletinConcursal>
                                <get:SBIF>
                                    <get:SBIFSummary>
                                        <get:TotalDebts/>
                                        <get:LatestFinancialDebt/>
                                        <get:DetailsCount>0</get:DetailsCount>
                                        <get:PresenceOfDetails>N</get:PresenceOfDetails>
                                    </get:SBIFSummary>
                                    <get:SBIFDetail/>
                                </get:SBIF>
                                <get:Justification/>
                            </get:Credit>
                            <get:Guarantees>
                                <get:Accreditations><get:AccreditationsFlag>NO</get:AccreditationsFlag><get:Vehicles><get:TotalNumberHeavyCars>0</get:TotalNumberHeavyCars><get:TotalNumberLightCars>0</get:TotalNumberLightCars><get:TotalNumberOtherCars>0</get:TotalNumberOtherCars><get:TotalNumberCars>0</get:TotalNumberCars><get:CarTaxValuation/><get:ComercialValuationCar/><get:CarActualizationDate>20210226</get:CarActualizationDate></get:Vehicles><get:PartnersAndCompanies><get:CountRelationshipsSociety>0</get:CountRelationshipsSociety><get:Societies/></get:PartnersAndCompanies><get:RealEstate><get:PropertiesCount>0</get:PropertiesCount><get:TotalAssesmentAmountPesos>0</get:TotalAssesmentAmountPesos></get:RealEstate><get:ExternalTrade><get:LastAmountExport/><get:LastAmountImport/><get:LastYearExport>00010101</get:LastYearExport><get:LastyearImport>00010101</get:LastyearImport></get:ExternalTrade><get:Gse><get:GseCode>N</get:GseCode><get:GseDate/><get:GseSource/></get:Gse><get:Sii><get:EconomicActivityDescription/><get:CategorySII/><get:StartSIIDate/><get:LastTaxPeriod/><get:LastTaxPeriodNumber/><get:Rubro/><get:InicioActividades/><get:DateUpdateInfoInicioAct/><get:UltimoTimbraje/><get:DateUpdateInfoUltimoTimbraje/><get:ObservacionesTributariasNumber>0</get:ObservacionesTributariasNumber><get:ObservacionesTributarias/></get:Sii></get:Accreditations>
                            </get:Guarantees>
                            <get:Behavior>
                                <get:Identification>
                                    <get:Age>36</get:Age>
                                    <get:DateOfBirth>19870315</get:DateOfBirth>
                                    <get:DeathDate/>
                                    <get:Discrepancies/>
                                    <get:FatherSurname>REYES</get:FatherSurname>
                                    <get:FlagDeath>0</get:FlagDeath>
                                    <get:FlagDeathDescription/>
                                    <get:FlagIdentityVerification/>
                                    <get:Gender>M</get:Gender>
                                    <get:GenderDescription>Masculino</get:GenderDescription>
                                    <get:InterdictDate/>
                                    <get:InterdictFlag>N</get:InterdictFlag>
                                    <get:MotherSurname>OYARZUN</get:MotherSurname>
                                    <get:Name>JONATHAN PATRICIO REYES OYARZUN</get:Name>
                                    <get:NameFull>JONATHAN PATRICIO</get:NameFull>
                                    <get:Nationality>CHILENA</get:Nationality>
                                    <get:NationalityType>C</get:NationalityType>
                                    <get:OtherInfo>
                                        <get:CodIse/>
                                        <get:DateUpdateFonasaInfo>00010101</get:DateUpdateFonasaInfo>
                                        <get:DateUpdateIse/>
                                        <get:DateUpdatePensionInfo/>
                                        <get:IsFonasa/>
                                        <get:PensionSolidaria/>
                                    </get:OtherInfo>
                                    <get:Rut>016522602K</get:Rut>
                                </get:Identification>
                                <get:Contactability>
                                    <get:AddressCount>0</get:AddressCount>
                                    <get:TelephoneCount>2</get:TelephoneCount>
                                    <get:Addresses>
                                        <get:AddressesType>
                                            <get:AddressDate>20130712</get:AddressDate>
                                            <get:AddressType>PARTICULAR</get:AddressType>
                                            <get:AditionalInfo/>
                                            <get:City>RANCAGUA</get:City>
                                            <get:CodeRegion>06</get:CodeRegion>
                                            <get:Communes>SAN VICENTE</get:Communes>
                                            <get:LastAddressVerificationDate/>
                                            <get:Number>532</get:Number>
                                            <get:PostalCode/>
                                            <get:Region>DEL LIBERTADOR BERNARDO OHIGGINS</get:Region>
                                            <get:SourceOfAddress>PARTICULAR - DIRECCIONES SIN VERIFICAR</get:SourceOfAddress>
                                            <get:Street>Connelly Bridge</get:Street>
                                            <get:StreetAndNumber>Connelly Bridge 532 </get:StreetAndNumber>
                                        </get:AddressesType>
                                    </get:Addresses>
                                    <get:Telephones>
                                        <get:TelephonesType>
                                            <get:Telephone>90731938</get:Telephone>
                                            <get:SourceOfTelephone/>
                                            <get:TelephoneDate/>
                                        </get:TelephonesType>
                                        <get:TelephonesType>
                                            <get:Telephone>78294507</get:Telephone>
                                            <get:SourceOfTelephone/>
                                            <get:TelephoneDate/>
                                        </get:TelephonesType>
                                    </get:Telephones>
                                </get:Contactability>
                                <get:Other>
                                    <get:Email/>
                                    <get:EmailDate/>
                                    <get:SourceOfEmail/>
                                    <get:WebSiteAvailableFlag>N</get:WebSiteAvailableFlag>
                                    <get:WebSiteURL/>
                                </get:Other>
                                <get:Family>
                                    <get:MaritalStatus>C</get:MaritalStatus>
                                    <get:MaritalStatusDescription>CASADO</get:MaritalStatusDescription>
                                    <get:SpouseRut>0178745018</get:SpouseRut>
                                    <get:DateOfMarriage>20160308</get:DateOfMarriage>
                                </get:Family>
                                <get:SRCeI>
                                    <get:BlockedCardLess30Days/>
                                    <get:BlockedStatusFlag>N</get:BlockedStatusFlag>
                                    <get:CodeExecution>00</get:CodeExecution>
                                    <get:DescExcecution>OK</get:DescExcecution>
                                    <get:DocumentStatus/><get:DocumentStatusReason/>
                                    <get:DocumentStatusTimestamp/>
                                    <get:InformationSource/>
                                    <get:InquiredSerialID/>
                                    <get:ReturnedSerialID/>
                                    <get:SerialNumberIndicator/>
                                </get:SRCeI>
                            </get:Behavior>
                            <get:Capacity>
                                <get:EmploymentInfo>
                                    <get:ProfessionCode>0</get:ProfessionCode>
                                    <get:ProfessionDescription>PROFESION NO CODIFICADA</get:ProfessionDescription>
                                    <get:RoleCode>0</get:RoleCode>
                                    <get:RoleDescription>PROFESION NO CODIFICADA</get:RoleDescription>
                                </get:EmploymentInfo>
                                <get:CurrentEmploymentInformation>
                                    <get:CompanyData>
                                        <get:Employer/>
                                        <get:VerificationSource/>
                                        <get:AddressOfTheEmployer/>
                                        <get:CityEmployerAddress/>
                                        <get:CommunesEmployerAddress/>
                                        <get:VerificationDate/>
                                        <get:ActualizationDate/>
                                        <get:LaboralTelephone/>
                                    </get:CompanyData>
                                    <get:Activity>
                                        <get:ActivityOfTheEmployer/>
                                    </get:Activity>
                                </get:CurrentEmploymentInformation>
                                <get:Historical/>
                                <get:Salary>
                                    <get:DateUpdatePublicEmployeeInfo/>
                                    <get:DateUpdateRentaInfo>20221102</get:DateUpdateRentaInfo>
                                    <get:DescCurrecy/>
                                    <get:IsPublicEmployee/>
                                    <get:RentaFuncionarioPublico/>
                                    <get:RentaPresunta>500000</get:RentaPresunta>
                                </get:Salary>
                            </get:Capacity>
                            <get:TransactionInfo>
                                <get:TransactionID/>
                                <get:TransactionTime/>
                            </get:TransactionInfo>
                        </get:response>
                    </get:getInformePlatinum360Response>
                </soapenv:Body>
            </soapenv:Envelope>'''.format(self.dicom_value_test)

    @api.onchange('service_type')
    def onchange_service_type(self):
        stage_ids = self.env['crm.stage'].search(['|', ('is_won', '=', True), ('name', '=', 'Perdida')])
        leads = self.env['crm.lead'].search([('stage_id', 'not in', stage_ids.ids),('partner_id', '=', self._origin.id)])
        for lead in leads:
            lead.service_type = self.service_type

    def cron_exception_status_dicom(self):
        date_today = datetime.now().date()
        for rec in self.search([('dicom_exception', '=', True), ('dicom_exception_date', '<', date_today)]):
            if date_today >= rec.dicom_exception_date:
                rec.status_exception_dicom = 'exception_due'
                rec.dicom_exception = False
                rec.onchange_dicom_exception()

    # @api.onchange('date_today')
    # def onchange_date_today(self):
    #     if self.date_today:
    #         stage_ids = self.env['crm.stage'].search(['|', ('is_won', '=', True), ('name', '=', 'Perdida')])
    #         leads = self.env['crm.lead'].search([('stage_id', 'not in', stage_ids.ids)])
    #         for lead in leads:
    #             lead.dicom_exception = self.dicom_exception
    #         if self.date_today >= self.dicom_exception_date:
    #             self.status_exception_dicom = 'exception_due'
    #             self.dicom_exception = False
    #
    # @api.onchange('date_today_test')
    # def onchange_date_today_test(self):
    #     if self.date_today:
    #         stage_ids = self.env['crm.stage'].search(['|', ('is_won', '=', True), ('name', '=', 'Perdida')])
    #         leads = self.env['crm.lead'].search([('stage_id', 'not in', stage_ids.ids)])
    #         for lead in leads:
    #             self.dicom_exception = lead.dicom_exception
    #         if self.date_today_test >= self.dicom_exception_date:
    #             self.status_exception_dicom = 'exception_due'
    #             self.dicom_exception = False

    @api.onchange('dicom_exception')
    def onchange_dicom_exception(self):
        if self.dicom_exception:
            stage_ids = self.env['crm.stage'].search(['|', ('is_won', '=', True), ('name', '=', 'Perdida')])
            leads = self.env['crm.lead'].search([('stage_id', 'not in', stage_ids.ids)])
            for lead in leads:
                lead.dicom_exception = self.dicom_exception
                lead.status_exception_dicom = 'exception'
            self.dicom_exception_date = datetime.now().date() + timedelta(days=30)
            self.status_exception_dicom = 'exception'
        elif not self.dicom_exception and self.date_today <= self.dicom_exception_date: ##   Cuando esta desactivado pero no esta vencido
            stage_ids = self.env['crm.stage'].search(['|', ('is_won', '=', True), ('name', '=', 'Perdida')])
            leads = self.env['crm.lead'].search([('stage_id', 'not in', stage_ids.ids)])
            for lead in leads:
                lead.dicom_exception = self.dicom_exception
                lead.status_exception_dicom = 'not_exception'
            self.status_exception_dicom = 'not_exception'
        elif not self.dicom_exception and self.date_today > self.dicom_exception_date: ## Cuando esta desactivada y esta vencida
            stage_ids = self.env['crm.stage'].search(['|', ('is_won', '=', True), ('name', '=', 'Perdida')])
            leads = self.env['crm.lead'].search([('stage_id', 'not in', stage_ids.ids)])
            for lead in leads:
                lead.dicom_exception = self.dicom_exception
                lead.status_exception_dicom = 'exception_due'
            self.status_exception_dicom = 'exception_due'

    @api.onchange('company_type')
    def onchange_company_type_dicom(self):
        frec = self.env.company.frequency
        dicom_last_score = 0
        dicom_last_date = False
        status = 'to_check'
        service_type = 'platinum' if self.company_type == 'person' else 'commercial'
        reports = self.dicom_report_ids.filtered(
            lambda x: x.partner_id.id == self.id and x.service_type == service_type) if self.dicom_report_ids else False
        last_report = reports[0] if reports else False
        if last_report and frec >= 0:
            diff = abs((fields.Date.today() - last_report.date.date()).days)
            if diff < frec:
                status = 'approved' if last_report.score >= self.env.company.approved else \
                    'check' if self.env.company.check and self.dicom_last_score < self.env.company.approved and self.dicom_last_score >= self.env.company.check else \
                        'rejected' if self.env.company.check and self.dicom_last_score < self.env.company.check else \
                            'rejected' if not self.env.company.check and self.dicom_last_score < self.env.company.approved else 'rejected' if self.dicom_last_score == 0 else 'to_check'
                dicom_last_score = last_report.score
                dicom_last_date = last_report.date.date()
        if self.company_type == 'person':
            self.write({
                'service_type': 'platinum',
                'dicom_last_score': dicom_last_score,
                'dicom_last_date': dicom_last_date,
                'status_dicom': status,
                'status_exception_dicom': 'not_exception',
                'dicom_exception': False,
                'dicom_exception_date': False
            })
        else:
            self.write({
                'service_type': 'commercial',
                'dicom_last_score': dicom_last_score,
                'dicom_last_date': dicom_last_date,
                'status_dicom': status,
                'status_exception_dicom': 'not_exception',
                'dicom_exception': False,
                'dicom_exception_date': False
            })

    def process_response_platinum(self, response):
        response_parsed = xmltodict.parse(response)
        code = response_parsed['soapenv:Envelope']['soapenv:Body']
        if 'get:getInformePlatinum360Response' in code:
            get_response = code['get:getInformePlatinum360Response']['get:response']
            get_credits = get_response['get:Credit']['get:DebtsSummary']
            get_identification = get_response['get:Behavior']['get:Identification']
            get_family = get_response['get:Behavior']['get:Family']
            get_acreditations = get_response['get:Guarantees']['get:Accreditations']
            get_vehicles = get_acreditations['get:Vehicles']
            get_companies = get_acreditations['get:PartnersAndCompanies']
            get_real_state = get_acreditations['get:RealEstate']
            get_external_trade = get_acreditations['get:ExternalTrade']
            get_sii = get_acreditations['get:Sii']
            get_contactability = get_response['get:Behavior']['get:Contactability']
            email = get_response['get:Behavior']['get:Other']['get:Email']
            everclean = get_response['get:Credit']['get:CreditRisk']['get:Everclean']
            date_everclean = get_response['get:Credit']['get:CreditRisk']['get:EvercleanDateUpdate']
            contactabilities = [get_contactability['get:Addresses']['get:AddressesType']] if isinstance(get_contactability['get:Addresses']['get:AddressesType'], dict) else get_contactability['get:Addresses']['get:AddressesType']
            xml_dict = {
                'risk': int(float(get_response['get:Credit']['get:CreditRisk']['get:PersonsRate'])),
                'name': get_identification['get:Name'],
                'namefull': get_identification['get:NameFull'],
                'motherSurname': get_identification['get:MotherSurname'],
                'fatherSurname': get_identification['get:FatherSurname'],
                'age': get_identification['get:Age'],
                'birthday': get_identification['get:DateOfBirth'],
                'rut': get_identification['get:Rut'],
                'gender': get_identification['get:GenderDescription'],
                'nac_type': get_identification['get:NationalityType'],
                'country_plat': get_identification['get:Nationality'],
                'maritalstatus': get_family['get:MaritalStatusDescription'],
                'spouserut': get_family['get:SpouseRut'],
                'contactabilities': contactabilities,
                'phone': get_contactability['get:Telephones']['get:TelephonesType'][0]['get:Telephone'],
                'email': email,
                'vehicles': get_vehicles,
                'companies': get_companies,
                'realstate': get_real_state,
                'external_trade': get_external_trade,
                'sii': get_sii,
                'credits': get_credits,
                'everclean': everclean,
                'date_everclean': date_everclean,
                ######### Categorías generales de la respuesta ############
                'Credit': get_response['get:Credit'],
                'Guarantees': get_response['get:Guarantees'],
                'Behavior': get_response['get:Behavior'],
                'Capacity': get_response['get:Capacity'],
                'TransactionInfo': get_response['get:TransactionInfo'],
            }
            return xml_dict
        if 'soapenv:Fault' in code:
            fail = code['soapenv:Fault']['detail']['con:fault']
            fault = {
                'code': fail['con:errorCode'],
                'reason': fail['con:reason']
            }
            raise UserError('Conexion DICOM\nError: %s \nMotivo: %s' % (fault['code'], fault['reason']))

    def process_response_commercial(self, response):
        #response_parsed = xmltodict.parse(response)
        if isinstance(response, str):
            response_parsed = json.loads(response)
        else: 
            response_parsed = response.json()
        commercial_data = response_parsed['data']['commercialData']
        behavior = commercial_data['behavior']
        guarantees = commercial_data['guarantees']
        identificacion = behavior['identification']
        credit_risk = commercial_data['credit']['creditRisk']
        sii = guarantees['accreditations']['sii']
        list_risk = []
        
        xml_dict = {
            'risk': int(float(credit_risk['personsRate'])),
            'list_risk': list_risk,
            'qty_doc': '0',  # identificacion['CantidadPrendas'],
            'amount_doc': '0',  # identificacion['CantidadQuiebras'],
            'name': identificacion['identificationCompany']['businessName'],
            'rut': identificacion['identificationCompany']['rut'],
            'activity': identificacion['identificationCompany']['activity'],
            'fantasy_name': identificacion['identificationCompany']['fantasyName'],
            'website': identificacion['identificationCompany']['webSite'],
            'email': identificacion['identificationCompany']['email'],
            'activity_description': sii['economicActivityDescription'],
            ######### Categorías generales de la respuesta ############
            'behavior': commercial_data['behavior'],
            'capacity': commercial_data['capacity'],
            'credit': commercial_data['credit'],
            'guarantees': commercial_data['guarantees'],
            'lanzamientosData': commercial_data['lanzamientosData'],
            'transactionInfo': commercial_data['transactionInfo'],

        }
        return xml_dict
        
    def commercial_authentiacion_metod(self, url):
        response_auth = requests.get(url + 'access', auth=(self.env.company.dicom_user, self.env.company.dicom_password))
        response_auth_parsed = response_auth.json()
        if response_auth.status_code != 200:
            raise UserError(response_auth.text)
        else:
            return response_auth_parsed

    def connect_dicom(self):
        xml_message = False
        if self.service_type == 'commercial':
            _logger.info('[2] Empresarial')
            rut = self.vat
            if '-' in self.vat:
                rut = self.vat.replace('-', '')
            else:
                raise UserError('El RUT debe estar separado por un guion')
            file_name = self.name + '.pdf'
            if self.env.company.status == 'qa':
                _logger.info('[3] QA')
                url = URL_DICOM_COMMERCIAL['qa']
            else:
                _logger.info('[3] Produccion')
                url = URL_DICOM_COMMERCIAL['prod']
            _logger.info('[4] ACCESS TOKEN')
            #### Authentiation ####
            response_auth = self.commercial_authentiacion_metod(url)
            _logger.info(response_auth)
            _logger.info('[5] OBTENER REPORTE')
            #### Consulta ####
            header = {
                'Authorization': 'Bearer %s' % response_auth['token']
            }
            url = url + 'v1/commercial-report/rut/' + rut
            _logger.info('URL Consulta: %s' % url)
            _logger.info('Bearer %s' % response_auth['token'])
            response = requests.get(url, headers=header)
            _logger.info(response)
            if response.status_code == 200:
                process_response = self.process_response_commercial(response)            
                self.write({
                    'dicom_last_score': process_response['risk'],
                    'dicom_last_date': date.today(),
                    'name': process_response['name'],
                    'fantasy_name': process_response['fantasy_name'],
                    'website': process_response['website'],
                    'l10n_cl_activity_description': process_response['activity_description'],
                })
                attach, b64_pdf = self.generate_pdf_commercial_file(process_response)
                return attach, b64_pdf, response
            else:
                return False, False, response
        if self.service_type == 'platinum':
            _logger.info('[2] Platinum')
            if '-' in self.vat:
                rut = self.vat.replace('-', '')
            else:
                raise UserError('El RUT debe estar separado por un guion')
            xml_message = self.env.ref('bm_crm_dicom_integration.report_platinum')._render({
                'user': self.env.company.dicom_user,
                'passwd': self.env.company.dicom_password,
                'rut': rut,
            })
            file_name = self.name + '.pdf'
            if self.env.company.status == 'qa':
                _logger.info('[3] Testing')
                url = URL_DICOM_PLATINUM['qa']
            else:
                _logger.info('[3] Produccion')
                url = URL_DICOM_PLATINUM['prod']
            headers = {
                'Content-Type': 'application/xml'
            }
            #files = {'archivo': (file_name, xml_message, 'text/xml')}
            _logger.info('[4] URL: %s' % url)
            response = requests.post(url, data=xml_message, headers=headers)
            if response.status_code == 200:
                process_response = self.process_response_platinum(response.text)
                self.write({
                    'dicom_last_score': process_response['risk'],
                    'dicom_last_date': date.today(),
                    'name': process_response['name'],
                    'full_name': process_response['namefull'],
                    'father_name': process_response['fatherSurname'],
                    'mother_name': process_response['motherSurname'],
                })
                attach, b64_pdf = self.generate_pdf_platinum_file(process_response)
                _logger.info(attach)
                _logger.info(b64_pdf)
                return attach, b64_pdf, response
            else:
                return False, False, False

    def connect_dicom_test(self):
        xml_message = False
        if self.service_type == 'commercial':
            _logger.info('[2] Empresarial')
            _logger.info('[3] QA LOCAL')
            response = self.empresarial()
            process_response = self.process_response_commercial(response)
            self.write({
                'dicom_last_score': process_response['risk'],
                'dicom_last_date': date.today(),
                #'name': process_response['name'],
                #'fantasy_name': process_response['fantasy_name'],
                #'website': process_response['website'],
                #'email': process_response['email']
            })
            attach, b64_pdf = self.generate_pdf_commercial_file(process_response)
            return attach, b64_pdf, response
        if self.service_type == 'platinum':
            _logger.info('[2] Platinum')
            _logger.info('[3] QA LOCAL')
            response = self.platinum()
            process_response = self.process_response_platinum(response)
            self.write({
                'dicom_last_score': process_response['risk'],
                'dicom_last_date': date.today(),
                #'name': process_response['name'],
            })
            attach, b64_pdf = self.generate_pdf_platinum_file(process_response)
            return attach, b64_pdf, response

    def generate_pdf_platinum_file(self, resp):
        report = self.env.ref('bm_crm_dicom_integration.action_report_dicomplatinum')
        pdf, format = report._render_qweb_pdf([self.id], data=resp)
        b64_pdf = base64.b64encode(pdf)
        ATTACHMENT_NAME = self.name
        attach_report = self.env['ir.attachment'].create({
            'name': ATTACHMENT_NAME + '.pdf',
            'type': 'binary',
            'datas': b64_pdf,
            'store_fname': ATTACHMENT_NAME + '.pdf',
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })
        #return b64_pdf
        return attach_report, b64_pdf

    def generate_pdf_commercial_file(self, resp):
        report = self.env.ref('bm_crm_dicom_integration.action_report_dicomcommercial')
        pdf, format = report._render_qweb_pdf([self.id], data=resp)
        b64_pdf = base64.b64encode(pdf)
        time = datetime.now(tz=None).time()
        dicom_date = datetime.combine(date.today(), time)
        ATTACHMENT_NAME = self.name + datetime.strftime(dicom_date, '%Y-%m-%d %H:%M')
        attach_report = self.env['ir.attachment'].create({
            'name': ATTACHMENT_NAME + '.pdf',
            'type': 'binary',
            'datas': b64_pdf,
            'store_fname': ATTACHMENT_NAME + '.pdf',
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })
        return attach_report, b64_pdf

    def action_request_dicom_report(self):
        DicomReport = self.env['dicom.report']
        HistoryDicom = self.env['history.request.dicom']
        # last_request = DicomReport.search([('partner_id', '=', self.partner_id.id)], limit=1)
        frec = self.env.company.frequency
        if self.dicom_last_date and frec >= 0:
            diff = abs((fields.Date.today() - self.dicom_last_date).days)
            # diff = abs((last_request.date - datetime.now()).days)
            if frec == 0:
                raise UserError('La configuracion actual no permite emitir un reporte Dicom')
            # elif diff > frec and not self.env.user.has_group('bm_crm_dicom_integration.group_crm_dicom_user_report'):
            #     raise UserError('No se puede emitir aun un reporte Dicom para este cliente.')
            elif diff < frec:
                last_report = self.dicom_report_ids[0] if self.dicom_report_ids else False
                if last_report:
                    status = 'approved' if last_report.score >= self.env.company.approved else \
                        'check' if self.env.company.check and last_report.score < self.env.company.approved and last_report.score >= self.env.company.check else \
                            'rejected' if self.env.company.check and last_report.score < self.env.company.check else \
                            'rejected' if not self.env.company.check and last_report.score < self.env.company.approved else 'rejected' if last_report.score == 0 else 'to_check'
                    values = {
                        'dicom_last_score': last_report.score,
                        'dicom_last_date': last_report.date.date(),
                        'status_dicom': status,
                    }
                    self.write(values)
                    if status == 'approved' and self.dicom_exception:
                        self.dicom_exception = False
                        self.onchange_dicom_exception()
                    return True
        _logger.info('[1] INICIANDO CONEXION CON DICOM')
        attach, b64_pdf, response = self.connect_dicom()
        if response.status_code == 200:
            _logger.info('GENERANDO HISTORIAL CONSULTA DICOM')
            history = HistoryDicom.create({
                'user_id': self.env.user.id,
                'partner_id': self.id,
                'request': response.text
            })
            self.history_dicom_id = history.id
            time = datetime.now(tz=None).time()
            dicom_date = datetime.combine(self.dicom_last_date, time)
            ATTACHMENT_NAME = self.name + datetime.strftime(dicom_date, '%Y-%m-%d %H:%M')
            vals = {
                'partner_id': self.id,
                'date': dicom_date,
                'service_type': self.service_type,
                'score': self.dicom_last_score,
                'user_id': self.env.user.id,
                'file_report_attachment': [(4, attach.id)],
                'file_report': b64_pdf,
                'file_name': ATTACHMENT_NAME + '.pdf',
                'history_dicom_id': history.id
            }
            if self.dicom_last_score >= self.env.company.approved:
                self.status_dicom = 'approved'

            elif self.env.company.check and self.dicom_last_score < self.env.company.approved and self.dicom_last_score >= self.env.company.check:
                self.status_dicom = 'check'
            elif self.env.company.check and self.dicom_last_score < self.env.company.check:
                self.status_dicom = 'rejected'
            else:
                self.status_dicom = 'rejected'
            DicomReport.create(vals)
        else:
            raise UserError(response.text)
        # file_pdf = self.generate_pdf_file(code, self.partner_id, self.dicom_last_date)

    def action_request_dicom_report_test(self):
        DicomReport = self.env['dicom.report']
        HistoryDicom = self.env['history.request.dicom']
        #last_request = DicomReport.search([('partner_id', '=', self.id)], limit=1)
        frec = self.env.company.frequency
        if self.dicom_last_date and frec >= 0:
        #if last_request:
            diff = abs((fields.Date.today() - self.dicom_last_date).days)
            if frec == 0:
                raise UserError('La configuracion actual no permite emitir un reporte Dicom')
            # if diff < frec and not self.env.user.has_group('bm_crm_dicom_integration.group_crm_dicom_user_report'):
            #     raise UserError('No se puede emitir aun un reporte Dicom para este cliente.')
            elif diff < frec:
                last_report = self.dicom_report_ids[0] if self.dicom_report_ids else False
                if last_report:
                    status = 'approved' if last_report.score >= self.env.company.approved else \
                        'check' if self.env.company.check and self.dicom_last_score < self.env.company.approved and self.dicom_last_score >= self.env.company.check else \
                            'rejected' if self.env.company.check and self.dicom_last_score < self.env.company.check else \
                            'rejected' if not self.env.company.check and self.dicom_last_score < self.env.company.approved else 'rejected' if self.dicom_last_score == 0 else'to_check'
                    values = {
                        'dicom_last_score': last_report.score,
                        'dicom_last_date': last_report.date.date(),
                        'status_dicom': status
                    }
                    self.write(values)
                    return True
        _logger.info('[1] INICIANDO CONEXION CON DICOM')
        attach, b64_pdf, response = self.connect_dicom_test()
        _logger.info('GENERANDO HISTORIAL CONSULTA DICOM')
        history = HistoryDicom.create({
            'user_id': self.env.user.id,
            'partner_id': self.id,
            'request': response
        })
        self.history_dicom_id = history.id
        time = datetime.now().time()
        dicom_date = datetime.combine(self.dicom_last_date, time)
        ATTACHMENT_NAME = self.name + datetime.strftime(dicom_date, '%Y-%m-%d %H:%M')
        vals = {
            'partner_id': self.id,
            'date': dicom_date,
            'service_type': self.service_type,
            'score': self.dicom_last_score,
            'user_id': self.env.user.id,
            'file_report_attachment': [(4, attach.id)],
            'file_report': b64_pdf,
            'file_name': ATTACHMENT_NAME + '.pdf',
            'history_dicom_id': history.id
        }
        if self.dicom_last_score >= self.env.company.approved:
            self.status_dicom = 'approved'
        elif self.env.company.check and self.dicom_last_score < self.env.company.approved and self.dicom_last_score >= self.env.company.check:
            self.status_dicom = 'check'
        elif self.env.company.check and self.dicom_last_score < self.env.company.check:
            self.status_dicom = 'rejected'
        else:
            self.status_dicom = 'rejected'
        DicomReport.create(vals)
        #file_pdf = self.generate_pdf_file(code, self.partner_id, self.dicom_last_date)

    def action_request_dicom_exception_report_test(self):
        DicomReport = self.env['dicom.report']
        HistoryDicom = self.env['history.request.dicom']
        _logger.info('[1] INICIANDO CONEXION CON DICOM')
        attach, b64_pdf, response = self.connect_dicom_test()
        _logger.info('GENERANDO HISTORIAL CONSULTA DICOM')
        history = HistoryDicom.create({
            'user_id': self.env.user.id,
            'partner_id': self.id,
            'request': response
        })
        self.history_dicom_id = history.id
        time = datetime.now().time()
        dicom_date = datetime.combine(self.dicom_last_date, time)
        ATTACHMENT_NAME = self.name + datetime.strftime(dicom_date, '%Y-%m-%d %H:%M')
        vals = {
            'partner_id': self.id,
            'date': dicom_date,
            'service_type': self.service_type,
            'score': self.dicom_last_score,
            'user_id': self.env.user.id,
            'file_report_attachment': [(4, attach.id)],
            'file_report': b64_pdf,
            'file_name': ATTACHMENT_NAME + '.pdf',
            'history_dicom_id': history.id
        }
        if self.dicom_last_score >= self.env.company.approved:
            self.status_dicom = 'approved'
        elif self.env.company.check and self.dicom_last_score < self.env.company.approved and self.dicom_last_score >= self.env.company.check:
            self.status_dicom = 'check'
        elif self.env.company.check and self.dicom_last_score < self.env.company.check:
            self.status_dicom = 'rejected'
        else:
            self.status_dicom = 'rejected'
        DicomReport.create(vals)

    def action_request_dicom_exception_report(self):
        DicomReport = self.env['dicom.report']
        HistoryDicom = self.env['history.request.dicom']
        _logger.info('[1] INICIANDO CONEXION CON DICOM')
        attach, b64_pdf, response = self.connect_dicom()
        if response:
            _logger.info('GENERANDO HISTORIAL CONSULTA DICOM')
            history = HistoryDicom.create({
                'user_id': self.env.user.id,
                'partner_id': self.id,
                'request': response
            })
            self.history_dicom_id = history.id
            time = datetime.now().time()
            dicom_date = datetime.combine(self.dicom_last_date, time)
            ATTACHMENT_NAME = self.name + datetime.strftime(dicom_date, '%Y-%m-%d %H:%M')
            vals = {
                'partner_id': self.id,
                'date': dicom_date,
                'score': self.dicom_last_score,
                'user_id': self.env.user.id,
                'file_report_attachment': [(4, attach.id)],
                'file_report': b64_pdf,
                'file_name': ATTACHMENT_NAME + '.pdf',
                'history_dicom_id': history.id
            }
            if self.dicom_last_score >= self.env.company.approved:
                self.status_dicom = 'approved'
            elif self.env.company.check and self.dicom_last_score < self.env.company.approved and self.dicom_last_score >= self.env.company.check:
                self.status_dicom = 'check'
            elif self.env.company.check and self.dicom_last_score < self.env.company.check:
                self.status_dicom = 'rejected'
            else:
                self.status_dicom = 'rejected'
            DicomReport.create(vals)

