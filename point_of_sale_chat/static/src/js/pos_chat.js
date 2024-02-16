odoo.define('point_of_sale_chat.chrome', function (require) {
"use strict";

    var chrome = require('point_of_sale.chrome');
    var config = require('web.config');
    var core = require('web.core');
    var session = require('web.session');
    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var gui = require('point_of_sale.gui');

    var Discuss = require('mail.Discuss');
    var QWeb = core.qweb;
    var _t = core._t;

    Discuss.include({
        _renderSidebar: function (options) {
            var self = this;
            if(!$('.o_mail_systray_item').hasClass('oe_hidden')){
                $('.o_mail_systray_item').addClass('oe_hidden');
            }
            var $Sidebar = this._super.apply(this, arguments);
            if (window.location.pathname == '/pos/web'){
                $Sidebar.find('div.back_to_pos').removeClass('hide').on("click",function(){
                    self.do_action("pos.ui");
                });
            }
            return $Sidebar;
        },
    });

    var MessageWidget = PosBaseWidget.extend({
        template:'MessageWidget',
        init: function(parent, options){
            options = options || {};
            this._super(parent,options);
        },
        events: {
            'click .o_mail_preview': '_onClickPreview',
            'click .o_filter_button': '_onClickFilterButton',
            'click .o_new_message': '_onClickNewMessage',
            'click .o_mail_preview_mark_as_read': '_onClickPreviewMarkAsRead',
            'click .o_thread_window_expand': '_onClickExpand',
            'click .close_chat': 'close'
        },
        isMobile: function () {
            return config.device.isMobile;
        },
        close: function(){
			if(!$('.o_mail_systray_item').hasClass('oe_hidden')){
		    	$('.o_mail_systray_item').addClass('oe_hidden');
		    }
        },
        /**
         * @override
         */
        willStart: function () {
            return $.when(this._super.apply(this, arguments), this.call('mail_service', 'isReady'));
        },
        /**
         * Opens the related document
         *
         * @private
         * @param {MouseEvent} ev
         */
        _onClickExpand: function (ev) {
            ev.stopPropagation();
            console.info(this)
            var $preview = $(ev.currentTarget).closest('.o_mail_preview');
            var documentModel = $preview.data('document-model');
            var documentID = $preview.data('document-id');
            this._openDocument(documentModel, documentID);
        },
        /**
         * @override
         */
        start: function () {
            this._$filterButtons = this.$('.o_filter_button');
            this._$previews = this.$('.o_mail_systray_dropdown_items');
            this._filter = false;
            this._updateCounter();
            var mailBus = this.call('mail_service', 'getMailBus');
            mailBus.on('update_needaction', this, this._updateCounter);
            mailBus.on('new_channel', this, this._updateCounter);
            mailBus.on('update_thread_unread_counter', this, this._updateCounter);
            return this._super.apply(this, arguments);
        },
        /**
         * Open the document
         *
         * @private
         * @param {string} documentModel the model of the document
         * @param {integer} documentID
         */
        _openDocument: function (documentModel, documentID) {
            if (documentModel === 'mail.channel') {
                this._openDiscuss(documentID);
            } else {
                var url = window.location.origin + "/web?#" +
                "id=" + documentID + "&model=" + documentModel +
                "&view_type=form&cids=" + $.bbq.getState().cids;
                window.open(url, '_blank');
            }
        },
        _updateCounter: function () {
            var counter = this._computeCounter();
            this.$('.o_notification_counter').text(counter);
            this.$el.toggleClass('o_no_notification', !counter);
                this._updatePreviews();
        },
        /**
         * Compute the counter next to the systray messaging menu. This counter is
         * the sum of unread messages in channels, the counter of the mailbox inbox,
         * and the amount of mail failures.
         *
         * @private
         * @returns {integer}
         */
        _computeCounter: function () {
            var channels = this.call('mail_service', 'getChannels');
            var channelUnreadCounters = _.map(channels, function (channel) {
                return channel.getUnreadCounter();
            });
            var unreadChannelCounter = _.reduce(channelUnreadCounters, function (acc, c) {
                return c > 0 ? acc + 1 : acc;
            }, 0);
            var inboxCounter = this.call('mail_service', 'getMailbox', 'inbox').getMailboxCounter();
            var mailFailureCounter = this.call('mail_service', 'getMailFailures').length;

            return unreadChannelCounter + inboxCounter + mailFailureCounter;
        },
        /**
         * Open the document
         *
         * @private
         * @param {string} documentModel the model of the document
         * @param {integer} documentID
         */
        _openDocument: function (documentModel, documentID) {
            if (documentModel === 'mail.channel') {
                this._openDiscuss(documentID);
            } else {
                var url = window.location.origin + "/web?#" +
                "id=" + documentID + "&model=" + documentModel +
                "&view_type=form&cids=" + $.bbq.getState().cids;
                window.open(url, '_blank');
            }
        },
        /**
         * @private
         * @param {MouseEvent} ev
         */
        _onClickFilterButton: function (ev) {
            ev.stopPropagation();
            this._$filterButtons.removeClass('active');
            var $target = $(ev.currentTarget);
            $target.addClass('active');
            this._filter = $target.data('filter');
            this._updatePreviews();
        },
        _updatePreviews: function () {
            // Display spinner while waiting for conversations preview
            this._$previews.html(QWeb.render('Spinner'));
            this._getPreviews()
                .then(this._renderPreviews.bind(this));
        },
        _getPreviews: function () {
            return this.call('mail_service', 'getSystrayPreviews', this._filter);
        },
        _renderPreviews: function (previews) {
            this._$previews.html(QWeb.render('mail.systray.MessagingMenu.Previews', {
                previews: previews,
            }));
        },
         _onClickNewMessage: function () {
            this.call('mail_service', 'openBlankThreadWindow');
        },
        _onClickPreviewMarkAsRead: function (ev) {
            ev.stopPropagation();
            var thread;
            var $preview = $(ev.currentTarget).closest('.o_mail_preview');
            var previewID = $preview.data('preview-id');
            if (previewID === 'mailbox_inbox') {
                var messageIDs = [].concat($preview.data('message-ids'));
                this.call('mail_service', 'markMessagesAsRead', messageIDs);
            } else if (previewID === 'mail_failure') {
                var documentModel = $preview.data('document-model');
                var unreadCounter = $preview.data('unread-counter');
                this.do_action('mail.mail_resend_cancel_action', {
                    additional_context: {
                        default_model: documentModel,
                        unread_counter: unreadCounter
                    }
                });
            } else {
                // this is mark as read on a thread
                thread = this.call('mail_service', 'getThread', previewID);
                if (thread) {
                    thread.markAsRead();
                }
            }
        },
        _onClickPreview: function (ev) {
            var $target = $(ev.currentTarget);
            var previewID = $target.data('preview-id');
            if (previewID === 'mail_failure') {
                this._clickMailFailurePreview($target);
            } else if (previewID === 'mailbox_inbox') {
                // inbox preview for non-document thread,
                // e.g. needaction message of channel
                var documentID = $target.data('document-id');
                var documentModel = $target.data('document-model');
                if (!documentModel) {
                    this._openDiscuss('mailbox_inbox');
                } else {
                    this._openDocument(documentModel, documentID);
                }
            } else {
                // preview of thread
                this.call('mail_service', 'openThread', previewID);
            }
        },
        _clickMailFailurePreview: function ($target) {
            var documentID = $target.data('document-id');
            var documentModel = $target.data('document-model');
            if (documentModel && documentID) {
                this._openDocument(documentModel, documentID);
            } else if (documentModel !== 'mail.channel') {
                // preview of mail failures grouped to different document of same model
                this.do_action({
                    name: "Mail failures",
                    type: 'ir.actions.act_window',
                    view_mode: 'kanban,list,form',
                    views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
                    target: 'current',
                    res_model: documentModel,
                    domain: [['message_has_error', '=', true]],
                });
            }
        },

    });
    gui.define_popup({name:'message', widget: MessageWidget});

    chrome.Chrome.include({
        events: {
            'click .pos_chat': '_onActivityMenuShow',
        },

        /**
         * @private
         */
        _onActivityMenuShow: function () {
             this.gui.show_popup('message',{});
        },

        
        build_widgets: function(){
            var self = this;
            this._super();
            if(self.pos.config.enable_pos_chat){
                $('div.pos_chat').show();
                $('div.pos_chat').find('i').attr('aria-hidden','false');
            }else{
                $('div.pos_chat').hide();
            }
        },
    });
});
