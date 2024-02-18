odoo.define("sh_activities_management.Manager.Notification", function (require) {
    "use strict";

    /**
     * Mail Notification Manager
     *
     * This part of the mail manager is responsible for receiving notifications on
     * the longpoll bus, which are data received from the server.
     */
    var MailManager = require("mail.Manager");
    var MailFailure = require("mail.model.MailFailure");
    var mail_Manager_Notification = require("mail.Manager.Notification");
    const config = require("web.config");
    var core = require("web.core");
    var session = require("web.session");

    var _t = core._t;
    MailManager.include({
        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * On receiving a notification that is specific to a user
         *
         * @private
         * @param {Object} data structure depending on the type
         * @param {integer} data.id
         */
        _handlePartnerNotification: function (data) {
            if (data.info === "unsubscribe") {
                this._handlePartnerUnsubscribeNotification(data);
            } else if (data.type === "toggle_star") {
                this._handlePartnerToggleStarNotification(data);
            } else if (data.type === "mark_as_read") {
                this._handlePartnerMarkAsReadNotification(data);
            } else if (data.type === "moderator") {
                this._handlePartnerMessageModeratorNotification(data);
            } else if (data.type === "author") {
                this._handlePartnerMessageAuthorNotification(data);
            } else if (data.type === "deletion") {
                this._handlePartnerMessageDeletionNotification(data);
            } else if (data.info === "transient_message") {
                this._handlePartnerTransientMessageNotification(data);
            } else if (data.type === "activity_updated") {
                this._handlePartnerActivityUpdateNotification(data);
            } else if (data.type === "mail_failure") {
                this._handlePartnerMailFailureNotification(data);
            } else if (data.type === "user_connection") {
                this._handlePartnerUserConnectionNotification(data);
            } else if (data.info === "channel_seen") {
                this._handlePartnerChannnelSeenNotification(data);
            } else if (data.type === "simple_notification") {
            	var title = _.escape(data.title);
                var message = _.escape(data.message);
                // softhealer custom code
                if (data.message) {
                    var str_msg = data.message.match("sh_simple_notification");
                    if (str_msg) {
                        //remove CODE_SH_SALE_PRICELIST_SIMPLE_NOTIFICATION_ from message and make valid message
                        message = data.message.replace("sh_simple_notification", "");
                    }
                }
                // softhealer custom code

                data.warning ? this.do_warn(title, message, data.sticky) : this.do_notify(title, message, data.sticky);
            } else if (data.info === "channel_minimize") {
                this._handlePartnerChannelMinimizeNotification(data);
            } else {
                this._handlePartnerChannelNotification(data);
            }
        },
    });

    return MailManager;
});
