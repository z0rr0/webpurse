/*
 for djago Cross Site Request Forgery protection (CSRF)
*/
$(document).ajaxSend(function(event, xhr, settings) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    function sameOrigin(url) {
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    function safeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});
// update left menu
function invoices_update(vurl, vdiv) {
    $.ajax({
        url: vurl,
        type: 'GET',
        dataType: 'html',
        context: document.body,
        async: true,
        success: function (data) {
            $(vdiv).html(data);
        },
        statusCode: {
            404: function() {
                $(vdiv).html('Page not found');
                // alert('Invoices page not found');
             },
        }
    });
}
// validate pays data
function val_validate(val_id) {
    str = $(val_id).val();
    str = str.replace(/,/gi, ".")
    val = parseFloat(str);
    if (isNaN(val) || val == 0) return false;
    else return val;
}
// send pay
function send_out(pref) {
    prefix = '#' + pref + '_';
    val = val_validate(prefix + 'value');
    if (!val) alert('Пожалуйста проверьте введенные значения.');
    else {
        // ok send form
        $.ajax({
            url: '/pay/add/',
            type: 'POST',
            data: {
                invoice : $(prefix + 'invoice').val(),
                itype : $(prefix + 'itype').val(),
                value : val,
                pdate : $('#datepicker_' + pref).val(),
                comment : $(prefix + 'comment').val(),
            },
            dataType: 'html',
            context: document.body,
            async: true,
            success: function (data) {
                invoices_update('/invoice/view/', '#leftm'); 
                alert("ok");
            },
            error: function () {
                alert('error'); 
            },
        });
        // clear form
        $(prefix + 'value').val(0);
        $(prefix + 'comment').val('');
    }
}