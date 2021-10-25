odoo.define('ks_dashboard_ninja.domain_fix', function(require) {

    "use strict";

    var BasicModel = require('web.BasicModel');
    var BasicFields = require('web.basic_fields');
    var view_dialogs = require('web.view_dialogs');
    var core = require("web.core");
    var Domain = require('web.Domain');

    var _t = core._t;

    // Whole Point of this file is to enable users to use %UID to calculate domain dynamically.
    BasicModel.include({

       _fetchSpecialDomain: function(record, fieldName, fieldInfo) {
            var self = this;
            var ks_allow_company_ids = []
            var ks_allow_company = this.getSession().user_companies.allowed_companies;
            for(var i = 0; i < ks_allow_company.length; i++) {
                ks_allow_company_ids.push(ks_allow_company[i][0]);
            }

            if (this.getSession().user_context.ks_allow_company_ids){
                var ks_allow_company_id = []
                this.getSession().user_context.allowed_company_ids.splice(0,this.getSession().user_context.allowed_company_ids.length)
                var ks_allow_company = this.getSession().user_context.ks_allow_company_ids;
                for(var i = 0; i < ks_allow_company.length; i++) {
                    ks_allow_company_id.push(ks_allow_company[i]);
                odoo.session_info.user_context.allowed_company_ids = ks_allow_company_id;
                }
            }


            var fieldName_temp = fieldName;
            if (record._changes && record._changes[fieldName]) {
                if (record._changes[fieldName].includes("%UID") || record._changes[fieldName].includes("%MYCOMPANY") || record._changes[fieldName].includes("%CIDS") || record._changes[fieldName].includes("%COMPANYIDS")) {
                    fieldName_temp = fieldName + '_temp';
                    record._changes[fieldName_temp] = record._changes[fieldName]
                    if (record._changes[fieldName_temp].includes("%UID")){
                        record._changes[fieldName_temp] = record._changes[fieldName_temp].replace('"%UID"', record.getContext().uid);
                    }
                    if (record._changes[fieldName_temp].includes("%MYCOMPANY")){

                        record._changes[fieldName_temp] = record._changes[fieldName_temp].replace('"%MYCOMPANY"', this.getSession().company_id)
                    }
                    if (record._changes[fieldName_temp].includes("%CIDS")){
                        if(this.getSession().user_context.ks_allow_company_ids === undefined){
                            this.getSession().user_context.ks_allow_company_ids = odoo.session_info.user_context.allowed_company_ids;
                        }
                        this.getSession().user_context.allowed_company_ids = ks_allow_company_ids;
                        record._changes[fieldName_temp] = record._changes[fieldName_temp].replace('"%CIDS"', this.getSession().company_id)
                    }
                if (record._changes[fieldName_temp].includes("%COMPANYIDS")){
                    if(this.getSession().user_context.ks_allow_company_ids === undefined){
                        this.getSession().user_context.ks_allow_company_ids = odoo.session_info.user_context.allowed_company_ids;
                    }
                        this.getSession().user_context.allowed_company_ids = ks_allow_company_ids;
                        record._changes[fieldName_temp] = record._changes[fieldName_temp].replace('"%COMPANYIDS"', JSON.stringify(ks_allow_company_ids))
                    }
                }

            } else if (record.data[fieldName] && (record.data[fieldName].includes("%UID") || record.data[fieldName].includes("%MYCOMPANY")|| record.data[fieldName].includes("%CIDS")|| record.data[fieldName].includes("%COMPANYIDS"))) {
                fieldName_temp = fieldName + '_temp';
                record.data[fieldName_temp] = record.data[fieldName];
                if (record.data[fieldName_temp].includes("%UID")){
                        record.data[fieldName_temp] = record.data[fieldName_temp].replace('"%UID"', record.getContext().uid);
                }
                if (record.data[fieldName_temp].includes("%MYCOMPANY")){
                    record.data[fieldName_temp] = record.data[fieldName_temp].replace('"%MYCOMPANY"', this.getSession().company_id)
                }
                if (record.data[fieldName_temp].includes("%CIDS")){
                    if(this.getSession().user_context.ks_allow_company_ids === undefined){
                        this.getSession().user_context.ks_allow_company_ids = odoo.session_info.user_context.allowed_company_ids;
                    }
                    this.getSession().user_context.allowed_company_ids = ks_allow_company_ids;
                    record.data[fieldName_temp] = record.data[fieldName_temp].replace('"%CIDS"', this.getSession().company_id)
                }
                if (record.data[fieldName_temp].includes("%COMPANYIDS")){
                    if(this.getSession().user_context.ks_allow_company_ids === undefined){
                        this.getSession().user_context.ks_allow_company_ids = odoo.session_info.user_context.allowed_company_ids;
                    }
                    this.getSession().user_context.allowed_company_ids = ks_allow_company_ids;
                    record.data[fieldName_temp] = record.data[fieldName_temp].replace('"%COMPANYIDS"', JSON.stringify(ks_allow_company_ids))
                }
            }
            return this._super(record,fieldName_temp,fieldInfo);
        },

    });

    BasicFields.FieldDomain.include({

        _onShowSelectionButtonClick: function(e) {
             var ks_allow_company_ids = []
            var ks_allow_company = this.getSession().user_companies.allowed_companies;
            for(var i = 0; i < ks_allow_company.length; i++) {
                ks_allow_company_ids.push(ks_allow_company[i][0]);
            }
            if (this.value && (this.value.includes("%CIDS") || this.value.includes("%COMPANYIDS") || this.value.includes("%MYCOMPANY") || this.value && this.value.includes("%UID")) ){
                var temp_value = this.value.includes("%MYCOMPANY") ? this.value.replace('"%MYCOMPANY"', this.getSession().company_id): this.value;
                 temp_value = temp_value.includes("%UID") ? temp_value.replace('"%UID"', this.record.getContext().uid): temp_value;
                 temp_value = temp_value.includes("%CIDS") ? temp_value.replace('"%CIDS"', this.getSession().company_id): temp_value;
                 temp_value = temp_value.includes("%COMPANYIDS") ? temp_value.replace('"%COMPANYIDS"', JSON.stringify(ks_allow_company_ids)): temp_value;
                e.preventDefault();
                new view_dialogs.SelectCreateDialog(this, {
                    title: _t("Selected records"),
                    res_model: this._domainModel,
                    domain: temp_value,
                    no_create: true,
                    readonly: true,
                    disable_multiple_selection: true,
                }).open();
            }else{
               this._super.apply(this, arguments);
            }
        },
    });

});