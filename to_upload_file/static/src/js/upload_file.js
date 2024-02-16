odoo.define('to_upload.UploadFile', function (require) {
    'use strict';

    var AbstractField = require('web.AbstractField');
    var registry = require('web.field_registry');
    var framework = require('web.framework');
    var Dialog = require('web.Dialog');
    var utils = require('web.utils');
    var core = require('web.core');

    var UploadFile = AbstractField.extend({
        supportedFieldTypes: ['char'],
        template: 'UploadFile',
        events: {
            'click .select_file_button, .input_show_file_name': '_onClickSelectFileButton',
            'change input[name="file"]': '_onFileChanged',
            'click .delete_file_button': '_onDeleteFileClick'
        },

        renderElement: function () {
            this._super.apply(this, arguments);
            this.$inputFile = this.$('input[type="file"]');
        },

        _getOriginalFileName: function () {
            return this.value.split('/').pop().slice(33);
        },

        _renderReadonly: function () {
            if (this.value) {
                if (this.recordData.id) {
                    this.$el.css('cursor', 'pointer');
                } else {
                    this.$el.css('cursor', 'not-allowed');
                }
                this.$('.download_file').append(this._getOriginalFileName());
            }
            if (!this.res_id) {
                this.$el.css('cursor', 'not-allowed');
            } else {
                this.$el.css('cursor', 'pointer');
            }
        },

        _renderEdit: function () {
            if (this.value) {
                this.$el.children().removeClass('d-none');
                this.$inputFile.addClass('d-none');
                this.$('.select_file_button').first().addClass('d-none');
                this.$('.input_show_file_name').val(this._getOriginalFileName());
            } else {
                this.$el.children().addClass('d-none');
                this.$('.select_file_button').first().removeClass('d-none');
            }
        },

        _onClickSelectFileButton: function (ev) {
            ev.stopPropagation();
            this.$inputFile.click();
        },

        _onFileChanged: function (ev) {
            ev.stopPropagation();
            this._uploadFile();
        },

        _uploadFile: function () {
            var self = this;
            var file = this.$inputFile[0].files[0];
            if (!file) {
                return;
            }

            var message = "Va a cargar el archivo " + file.name + " (" + utils.human_size(file.size) + "), está seguro?";
            Dialog.confirm(this, message, {
                confirm_callback: () => {
                    self._doUploadFile(file);
                }
            });
        },

        _doUploadFile: function (file) {
            var self = this;
            framework.blockUI();
            var formData = new FormData();
            formData.append('file', file);
            formData.append('csrf_token', core.csrf_token);
            return fetch('/to_upload_file/upload', {
                method: 'POST',
                body: formData
            }).then(response => {
                if (response.ok) {
                    return response.json();
                }
                throw response;
            }).then(result => {
                if (result.file_path) {
                    self._setValue(result.file_path);
                    self.filename = file.name;
                } else {
                    throw result;
                }
            }).catch(error => {
                console.error(error);
                var errorDialog = new Dialog(self, {
                    title: 'Error',
                    $content: $('<p>Failed to upload file ' + file.name + '!</p>'),
                    size: 'medium',
                    buttons: [
                        {
                            text: 'Retry',
                            close: true,
                            classes: 'btn-primary',
                            click: () => {
                                self._doUploadFile(file);
                            }
                        },
                        {
                            text: 'Cancel',
                            close: true
                        }
                    ]
                });
                errorDialog.open();
            }).finally(() => {
                framework.unblockUI();
            })
        },

        _onDeleteFileClick: function() {
            const self = this;
            this._setValue(false).then(() => self._render());
        }
    });
    registry.add('upload_file', UploadFile);

    return UploadFile;
});