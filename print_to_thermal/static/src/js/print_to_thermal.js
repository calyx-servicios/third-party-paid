odoo.define('print_to_thermal.widget', function (require) {
  var core = require('web.core');
  var ActionManager= require('web.ActionManager');
  const Device = require('print_to_thermal.device');
  const DropdownMenu = require('web.DropdownMenu');
  var framework = require('web.framework');
  var utils = require('web.utils');
  var session = require('web.session');
  const ActionMenus = require('web.ActionMenus')

  var thermal_printers = {};
  var _t = core._t;

  ActionManager.include({
    _downloadReportThermal: function (url, actions) {
        var self = this;
        var cloned_action = _.clone(actions);

        framework.blockUI();

        var thermal_url = 'report/thermal/' + cloned_action.report_name;
        if (_.isUndefined(cloned_action.data) ||
            _.isNull(cloned_action.data) ||
            (_.isObject(cloned_action.data) && _.isEmpty(cloned_action.data)))
        {
            if (cloned_action.context.active_ids) {
                thermal_url += "/" + cloned_action.context.active_ids.join(',');
            }
        } else {
            thermal_url += '?options=' + encodeURIComponent(JSON.stringify(cloned_action.data));
            thermal_url += '&context=' + encodeURIComponent(JSON.stringify(cloned_action.context));
        }

        var postData = new FormData();
        if (core.csrf_token) {
           postData.append('csrf_token', core.csrf_token);
        }

        var xhr = new XMLHttpRequest();

        return new Promise(function (resolve, reject) {
            $.ajax(thermal_url, {
                xhr: function() {return xhr;},
                data: postData,
                processData:    false,
                contentType:    false,
                type:           'POST'
            }).then(function (data) {
                framework.unblockUI();
                var xml = new XMLSerializer().serializeToString(data.documentElement);
                if(!xml){
                    self.do_warn(_t('Warning'), _t("Malformed XML"), true);
                    reject();
                }
                var active_printer = localStorage.getItem("active_printer");
                if(thermal_printers[active_printer] && thermal_printers[active_printer].proxy.get('status').status === 'connected'){
                    thermal_printers[active_printer].print_receipt(xml);
                }else{
                    self.do_warn(_t('Warning'), _t("There is not an active printer, check printers connection"), true);
                    reject();
                }
                resolve();
            }).fail(function (error) {framework.unblockUI(); self.do_warn(_t('rpc_error'), error, true); framework.unblockUI();reject();});

        })

     },
    _triggerDownload: function (action, options, type) {
        var self = this;
        var reportUrls = this._makeReportUrls(action);
        if (type === "qweb-thermal" || type === 'qweb-thermal_remote') {
            return self._downloadReportThermal(reportUrls[type], action).then(function () {
                if (action.close_on_report_download) {
                    var closeAction = {type: 'ir.actions.act_window_close'};
                    return self.doAction(closeAction, _.pick(options, 'on_close'));
                } else {
                    return options.on_close();
                }
            });
        }
        return this._super.apply(this, arguments);
    },
    _makeReportUrls: function (action) {
        var reportUrls = this._super.apply(this, arguments);
        reportUrls.thermal = '/report/thermal/' + action.report_name;
        return reportUrls;
    },
    _executeReportAction: function (action, options) {
        var self = this;
        if (action.report_type === 'qweb-thermal' || action.report_type === 'qweb-thermal_remote') {
            return self._triggerDownload(action, options, 'qweb-thermal');
        }
        return this._super.apply(this, arguments);
    }
  });

  class Printer {
    constructor(options){
        this.options = _.defaults(options || {}, {});
        this.init_connection()
    }

    init_connection(){
        this.proxy = new Device.ProxyDevice(this, this.options);
        return this.proxy.autoconnect({
              force_ip: this.options.url || undefined,
          });
    }

    print_receipt(receipt){
      if(this.proxy.get('status').status !== 'connecting' && this.proxy.get('status').status !== 'connected'){
        this.proxy.reconnect().then(function(){
            this.proxy.print_receipt(receipt);
          });
        }else{
          this.proxy.print_receipt(receipt);
        }
    }

    disconnect  (){
      this.proxy.disconnect();
    }
  }

  utils.patch(ActionMenus, 'print_to_thermal.PrintToThermalActionMenus', {

    async willStart() {
      await this._super(...arguments);
      this.printerItems = await this._setPrinterItems(this.props);
      this.showThermal = await this._showThermal()
    },
    async willUpdateProps(nextProps) {
      await this._super(...arguments);
      this.printerItems = await this._setPrinterItems(this.props);
      this.showThermal = await this._showThermal()
    },
    _showThermal(){
        if(this.props.items.print){
            for(var i in this.props.items.print){
              if(this.props.items.print[i].report_type === 'qweb-thermal' || this.props.items.print[i].report_type === 'thermal_remote'){
                return true;
              }
            }
        }
        return false;
    },
    async _setPrinterItems(props){
      var self = this;
      let printerItems = [];
        var params = {}
        let printers = []
        params = await self.rpc({
          route: '/web/report/thermal/params'
        })
        if (params['thermal.printer_urls'] && params['thermal.printer_urls'] !== '' && params['thermal.printer_urls'] !== '[]' && params['thermal.printer_urls'].length !== 0){
          printers = params['thermal.printer_urls'].split(',');
        }
        if (window.isMobilePos)
        {
          printers = [];
          params['thermal.default_printer'] = 'MobilePos';
          localStorage.setItem('active_printer', 'MobilePos');
        }
        if (printers.length === 0 && !params['thermal.default_printer']){
          return [{description: _t('No printer configured')}];
        }
        if(!(params['thermal.default_printer'] in printers)){
          printers.push(params['thermal.default_printer']);
        }
        var default_printer = localStorage.getItem("active_printer");
        if (!default_printer || default_printer === '' || default_printer === 'false' || !printers[default_printer]){
            default_printer = params['thermal.default_printer'];
        }
        for (var x in printers){
          if (printers[x]){
            var data = {'url': printers[x], 'timeout_val': params['thermal.time_alive_printer']};
            if (printers[x] == default_printer){
              data.keptalive = true;
            }
            let thermal_printer = new Printer(data);
            thermal_printers[printers[x]] = thermal_printer;
            let status = thermal_printer.proxy.get('status').status;
            printerItems.push(
            {
                id: printers[x].replace('.', '_').replace('.', '_').replace('.', '_').replace(':', '').replace('/', '_').replace('/', '_'),
                description: _t('Set as active: ' + printers[x] + ' - ')  + status,
                thermal: printers[x]
            });
          }
        }
        localStorage.setItem('active_printer', default_printer);

      return printerItems;
    }

  })


  class PrintToThermalMenu extends DropdownMenu {
    async willStart(){

    }
    async willUpdateProps(nextProps){

    }

    start(){
      var self = this;
      self.$el.on('click', '.btn_thermal_status', function() {
           _.each(thermal_printers, function(printer, printer_o){
              self.$el.find("#thermal_" + printer.options.url.replace('.', '_').replace('.', '_').replace('.', '_').replace(':', '').replace('/', '_').replace('/', '_')).html(printer.proxy.get('status').status)
           })
        });
    }

    _onItemSelected(ev) {
      ev.stopPropagation();
      const { item } = ev.detail;
      if (item.thermal){
        var therm = localStorage.getItem('active_printer');
        if(thermal_printers[therm]){
          thermal_printers[therm].proxy.killalive();
        }
        thermal_printers[item.thermal].proxy.keepalive();
        localStorage.setItem('active_printer', item.thermal);
      }
    }


  }
  PrintToThermalMenu.template = 'print_to_thermal.PrintToThermalMenu';

  ActionMenus.components['PrintToThermalMenu'] = PrintToThermalMenu;
});
