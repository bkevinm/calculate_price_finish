flectra.define('calculate_price.CalculatePrice', function (require) {
    "use strict";

    var rpc = require("web.rpc");
    require('website_sale.website_sale');
    var ajax = require('web.ajax');
    var publicWidget = require('web.public.widget');
    const wUtils = require('website.utils');

    $(document).ready(function () {
        var objectWidth = $("#width_c");
        var objectHeight = $("#height_c");
        var actuaWidth = parseInt(objectWidth.val());
        var actuaHeight = parseInt(objectHeight.val());
        var objectAmount = $('.oe_currency_value');
        var minWidth = objectWidth.attr('min');
        var minHeight = objectHeight.attr('min');

        checkMins();

        objectWidth.change(function (ev) {
            var val = parseInt(objectWidth.val());
            if (val < minWidth) {
                objectWidth.val(minWidth);
            } else {
                recalculateAll();
            }
        });

        objectHeight.change(function (ev) {
            var val = parseInt(objectHeight.val());
            if (val < minHeight) {
                objectHeight.val(minHeight);
            } else {
                recalculateAll();
            }
        });

        objectAmount.on('DOMSubtreeModified', function () {
            recalculateAll();
        });

        function checkMins() {
            if (actuaWidth < minWidth) {
                objectWidth.val(minWidth);
            }
            if (actuaHeight < minHeight) {
                objectHeight.val(minHeight);
            }
            recalculateAll();
        }

        function recalculateAll() {
            $.ajax({
                url: "/products/calculate_price",
                type: "POST",
                contentType: "application/json",
                data: `{"params": {"product_id": ${$('.product_id').val() || 0}, "width": ${parseFloat(objectWidth.val()) || 0}, "height":${parseFloat(objectHeight.val()) || 0}}}`,
            }).done(function (result) {
                var cubes = result['result'];
                if (objectAmount.html() != undefined){
                    $('.actual_price_cp').html(`$ ${(parseFloat(cubes) * parseFloat((objectAmount.html()).replace(",","")))}`);
                }
            });
        }

        publicWidget.registry.WebsiteSale.include({
            events: _.extend({}, publicWidget.registry.WebsiteSale.prototype.events),

            _submitForm: function () {
                let params = this.rootProduct;
                params.add_qty = params.quantity;

                params.product_custom_attribute_values = JSON.stringify(params.product_custom_attribute_values);
                params.no_variant_attribute_values = JSON.stringify(params.no_variant_attribute_values);
                params.width_c = parseFloat(objectWidth.val()) | 0;
                params.height_c = parseFloat(objectHeight.val()) | 0;

                if (this.isBuyNow) {
                    params.express = true;
                }

                return wUtils.sendRequest('/shop/cart/update', params);
            },
        });
    });
});

