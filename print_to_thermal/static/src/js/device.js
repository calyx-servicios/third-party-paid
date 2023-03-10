odoo.define('print_to_thermal.device', function (require) {
  var core = require('web.core');
  var mixins = require('web.mixins');
  var Session = require('web.Session');

  var QWeb = core.qweb;
  var _t = core._t;

  var ProxyDevice  = core.Class.extend(mixins.PropertiesMixin,{
      init: function(parent, options){
          mixins.PropertiesMixin.init.call(this, parent);
          var self = this;
          options = options || {};
          this.weighing = false;
          this.debug_weight = 0;
          this.use_debug_weight = false;

          this.paying = false;
          this.default_payment_status = {
              status: 'waiting',
              message: '',
              payment_method: undefined,
              receipt_client: undefined,
              receipt_shop:   undefined,
          };
          this.custom_payment_status = this.default_payment_status;

          this.receipt_queue = [];

          this.notifications = {};
          this.bypass_proxy = false;

          this.connection = null;
          this.host       = options.url;
          this.keptalive  = false;
          this.keepalive_var  = false;
          this.isMobilePos = options.url === 'MobilePos';

          this.set('status',{});

          this.set_connection_status('disconnected');

          this.on('change:status',this,function(eh,status){
              status = status.newValue;
              if(status.status === 'connected'){
                  if (self.keptalive){
                    self.keepalive();
                  }
                  self.print_receipt();
              }
          });
          var timeout_val = 5000;
          if (options.timeout_val){
              timeout_val = options.timeout_val * 1000;
          }
          this.timeout_val = timeout_val;
      },
      set_connection_status: function(status,drivers){
          var oldstatus = this.get('status');
          var newstatus = {};
          newstatus.status = status;
          newstatus.drivers = status === 'disconnected' ? {} : oldstatus.drivers;
          newstatus.drivers = drivers ? drivers : newstatus.drivers;
          this.set('status',newstatus);
      },
      disconnect: function(){
          if(this.get('status').status !== 'disconnected'){
              this.connection.destroy();
              this.set_connection_status('disconnected');
          }
      },

      // connects to the specified url
      connect: function(url){
          var self = this;
          this.set_connection_status('connecting',{});
          if(this.isMobilePos){
            return this.message('handshake').then(function(response){
                  if(response){
                      self.set_connection_status(window.printer_status);
                      localStorage.hw_proxy_url = url;
                      self.keepalive();
                  }else{
                      self.set_connection_status('disconnected');
                      console.error('Connection refused by the Proxy');
                  }
                },function(){
                    self.set_connection_status('disconnected');
                    console.error('Could not connect to the Proxy');
                });
          }
          this.connection = new Session(undefined, url, { use_cors: true});
          this.host = url;

          return this.message('handshake').then(function(response){
                  if(response){
                      self.set_connection_status('connected');
                  }else{
                      self.set_connection_status('disconnected');
                      console.error('Connection refused by the Proxy');
                  }
              },function(){
                  self.set_connection_status('disconnected');
                  console.error('Could not connect to the Proxy');
              });
      },

      // find a proxy and connects to it. for options see find_proxy
      //   - force_ip : only try to connect to the specified ip.
      //   - port: what port to listen to (default 8069)
      //   - progress(fac) : callback for search progress ( fac in [0,1] )
      autoconnect: function(options){
          var self = this;
          this.set_connection_status('connecting',{});
          if(this.isMobilePos){
            return self.connect('/hw_proxy/hello');
          }
          var found_url = new Promise(function () {});

          if ( options.force_ip ){
              // if the ip is forced by server config, bailout on fail
              found_url = this.try_hard_to_connect(options.force_ip, options);
          }else if( localStorage.hw_proxy_url ){
              // try harder when we remember a good proxy url
              found_url = this.try_hard_to_connect(localStorage.hw_proxy_url, options)
                  .then(null,function(){
                    if (window.location.protocol != 'https:'){
                        return self.find_proxy(options);
                    }
                  });
          }else{
            // just find something quick
            if (window.location.protocol != 'https:'){
                found_url = this.find_proxy(options);
            }
          }

          var successProm = found_url.then(function (url) {
              return self.connect(url);
          });

          successProm.catch(function () {
              self.set_connection_status('disconnected');
          });

        return successProm;
      },

      // starts a loop that updates the connection status
      keepalive: function(){
          var self = this;
          if(this.isMobilePos){
            function status(){
              self.set_connection_status(window.printer_status, {'escpos': {'status': window.printer_status}});
              setTimeout(status, self.timeout_val);
            }
          }else{
            function status(){
              self.connection.rpc('/hw_proxy/status_json',{},{timeout:2500})
                  .then(function(driver_status){
                      self.set_connection_status('connected',driver_status);
                  },function(){
                      if(self.get('status').status !== 'connecting'){
                          self.set_connection_status('disconnected');
                      }
                  }).always(function(){
                      setTimeout(status, self.timeout_val);
                  });
                }
          }
        self.keepalive_var = status;
        self.keepalive_var();
      },
      killalive: function(){
        var self = this;
        clearTimeout(self.keepalive_var);
      },
      message : function(name, params){
          var callbacks = this.notifications[name] || [];
          for(var i = 0; i < callbacks.length; i++){
              callbacks[i](params);
          }
          if(this.isMobilePos){
            if(this.get('status').status !== 'disconnected'){
                var mess = 'correct';
                if(name === 'print_xml_receipt'){
                  window.ReactNativeWebView.postMessage("REACT_PRINT_XML"+params.receipt);
                }
                return Promise.reject();
            }else{
                return Promise.reject();
            }
          }
          if(this.get('status').status !== 'disconnected'){
              return this.connection.rpc('/hw_proxy/' + name, params || {}, {shadow: true});
          }else{
              return Promise.reject();
          }
      },
      reconnect: function(){
        var self = this;
        self.connect(self.url);
      },

      // try several time to connect to a known proxy url
      try_hard_to_connect: function(url,options){
          options   = options || {};
          var protocol = window.location.protocol;
          var port = ( !options.port && protocol == "https:") ? ':443' : ':' + (options.port || '8069');

          this.set_connection_status('connecting');

          if(url.indexOf('//') < 0){
              url = protocol + '//' + url;
          }

          if(url.indexOf(':',5) < 0){
              url = url + port;
          }

          // try real hard to connect to url, with a 1sec timeout and up to 'retries' retries
          function try_real_hard_to_connect(url, retries) {

              return Promise.resolve(

              $.ajax({
                  url: url + '/hw_proxy/hello',
                  method: 'GET',
                  timeout: 1000,
              })
              .then(function () {
                    return Promise.resolve(url);
              }, function (resp) {
                    if (retries > 0) {
                        return try_real_hard_to_connect(url, retries-1);
                    } else {
                        return Promise.reject([resp.statusText, url]);
                    }
                })
              )
          }

          return try_real_hard_to_connect(url,3);
      },

      // returns as a deferred a valid host url that can be used as proxy.
      // options:
      //   - port: what port to listen to (default 8069)
      //   - progress(fac) : callback for search progress ( fac in [0,1] )
      find_proxy: function(options){
          options = options || {};
          var self  = this;
          var port  = ':' + (options.port || '8069');
          var urls  = [];
          var found = false;
          var parallel = 8;
          var done = new $.Deferred(); // will be resolved with the proxies valid urls
          var threads  = [];
          var progress = 0;


          urls.push('http://localhost'+port);
          for(var i = 0; i < 256; i++){
              urls.push('http://192.168.0.'+i+port);
              urls.push('http://192.168.1.'+i+port);
              urls.push('http://10.0.0.'+i+port);
          }

          var prog_inc = 1/urls.length;

          function update_progress(){
              progress = found ? 1 : progress + prog_inc;
              if(options.progress){
                  options.progress(progress);
              }
          }

          function thread(done){
              var url = urls.shift();

              done = done || new $.Deferred();

              if( !url || found || !self.searching_for_proxy ){
                  done.resolve();
                  return done;
              }

              $.ajax({
                      url: url + '/hw_proxy/hello',
                      method: 'GET',
                      timeout: 400,
                  }).done(function(){
                      found = true;
                      update_progress();
                      done.resolve(url);
                  })
                  .fail(function(){
                      update_progress();
                      thread(done);
                  });

              return done;
          }

          this.searching_for_proxy = true;

          var len  = Math.min(parallel,urls.length);
          for(i = 0; i < len; i++){
              threads.push(thread());
          }

          $.when.apply($,threads).then(function(){
              var urls = [];
              for(var i = 0; i < arguments.length; i++){
                  if(arguments[i]){
                      urls.push(arguments[i]);
                  }
              }
              done.resolve(urls[0]);
          });

          return done;
      },

      stop_searching: function(){
          this.searching_for_proxy = false;
          this.set_connection_status('disconnected');
      },

      // this allows the client to be notified when a proxy call is made. The notification
      // callback will be executed with the same arguments as the proxy call
      add_notification: function(name, callback){
          if(!this.notifications[name]){
              this.notifications[name] = [];
          }
          this.notifications[name].push(callback);
      },

      // sets a custom weight, ignoring the proxy returned value.
      debug_set_weight: function(kg){
          this.use_debug_weight = true;
          this.debug_weight = kg;
      },

      // resets the custom weight and re-enable listening to the proxy for weight values
      debug_reset_weight: function(){
          this.use_debug_weight = false;
          this.debug_weight = 0;
      },

      // ask for the cashbox (the physical box where you store the cash) to be opened
      open_cashbox: function(){
          return this.message('open_cashbox');
      },

      /*
       * ask the printer to print a receipt
       */
      print_receipt: function(receipt){
          var self = this;
          if(receipt){
              this.receipt_queue.push(receipt);
          }
          function send_printing_job(){
              if (self.receipt_queue.length > 0){
                  var r = self.receipt_queue.shift();
                  self.message('print_xml_receipt',{ receipt: r },{ timeout: 5000 })
                      .then(function(){
                          send_printing_job();
                      },function(error){
                          if (error) {
                              self.do_warn(_t('Printing Error: ') + error.data.message, error.data.debug);
                              return;
                          }
                          self.receipt_queue.unshift(r);
                      });
              }
          }
          send_printing_job();
      },

      update_customer_facing_display: function(html) {
          if (this.posbox_supports_display) {
              return this.message('customer_facing_display',
                  { html: html },
                  { timeout: 5000 });
          }
      },

      take_ownership_over_client_screen: function(html) {
          return this.message("take_control", { html: html });
      },

      test_ownership_of_client_screen: function() {
          if (this.connection) {
              return this.message("test_ownership", {});
          }
          return null;
      },

      // asks the proxy to log some information, as with the debug.log you can provide several arguments.
      log: function(){
          return this.message('log',{'arguments': _.toArray(arguments)});
      },

  });

  return {
      ProxyDevice: ProxyDevice,
  };
});
