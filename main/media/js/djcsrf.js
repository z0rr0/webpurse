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
function up_view(el) {
    el.style.opacity="1";
}
function down_view(el) {
    el.style.opacity="0.5";
}
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
        error: function () {
                alert('sorry, error'); 
            },
    });
}
// validate pays data
function val_validate(val_id, force) {
    str = $(val_id).val();
    str = jQuery.trim(str.replace(/,/gi, "."));
    $(val_id).val(str);
    if (force) val = parseFloat(str);
    else val = str;
    // if
    if (isNaN(val) || val == 0) return false;
    else return val;
}
// send pay
function send_out(pref) {
    prefix = '#' + pref + '_';
    val = val_validate(prefix + 'value', true);
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
                $(prefix + 'status').html('Сохранено');
                $(prefix + 'status').show();
                invoices_update('/invoice/view/', '#leftm'); 
                $(prefix + 'status').hide(8000);
                get_pay_last('#pay_last');
                // alert("ok");
            },
            error: function () {
                alert('sorry, error'); 
            },
        });
        // clear form
        $(prefix + 'value').val(0);
        $(prefix + 'comment').val('');
    }
}
// send corrent pay
function send_cor(pref) {
    prefix = '#' + pref + '_';
    val = val_validate(prefix + 'value', true);
    if (!val) alert('Пожалуйста проверьте введенные значения.');
    else {
        if ($(prefix + 'tosum').is(':checked')) tosum = 1;
        else tosum = 0;
        // ok send form
        $.ajax({
            url: '/pay/correct/',
            type: 'POST',
            data: {
                invoice : $(prefix + 'invoice').val(),
                tosum : tosum,
                value : val,
                pdate : $('#datepicker_' + pref).val(),
                comment : $(prefix + 'comment').val(),
            },
            dataType: 'html',
            context: document.body,
            async: true,
            success: function (data) {
                $(prefix + 'status').html('Сохранено');
                $(prefix + 'status').show();
                invoices_update('/invoice/view/', '#leftm'); 
                $(prefix + 'status').hide(8000);
                get_pay_last('#pay_last');
                // alert("ok");
            },
            error: function () {
                alert('sorry, error'); 
            },
        });
        // clear form
        $(prefix + 'value').val(0);
        $(prefix + 'comment').val('');
    }
}
// send transfer pay
function send_trans(pref) {
    prefix = '#' + pref + '_';
    val = val_validate(prefix + 'value', true);
    if (!val) alert('Пожалуйста проверьте введенные значения.');
    else {
        // ok send form
        $.ajax({
            url: '/transfer/add/',
            type: 'POST',
            data: {
                ifrom : $(prefix + 'ifrom').val(),
                ito : $(prefix + 'ito').val(),
                value : val,
                pdate : $('#datepicker_' + pref).val(),
                comment : $(prefix + 'comment').val(),
            },
            dataType: 'html',
            context: document.body,
            async: true,
            success: function (data) {
                $(prefix + 'status').html('Сохранено');
                $(prefix + 'status').show();
                invoices_update('/invoice/view/', '#leftm'); 
                $(prefix + 'status').hide(8000);
                get_trans_last('#pay_last');
                // alert("ok");
            },
            error: function () {
                alert('sorry, error'); 
            },
        });
        // clear form
        $(prefix + 'value').val(0);
        $(prefix + 'comment').val('');
    }
}
// send dept
function send_depts(pref) {
    prefix = '#' + pref + '_';
    val = val_validate(prefix + 'value', true);
    if (!val) alert('Пожалуйста проверьте введенные значения.');
    else {
        if ($(prefix + 'credit').is(':checked')) credit = 1;
        else credit = 0;
        // ok send form
        $.ajax({
            url: '/dept/add/',
            type: 'POST',
            data: {
                value : val,
                invoice : $(prefix + 'invoice').val(),
                taker : $(prefix + 'taker').val(),
                credit : credit,
                pdate : $('#datepicker_' + pref).val(),
                comment : $(prefix + 'comment').val(),
            },
            dataType: 'html',
            context: document.body,
            async: true,
            success: function (data) {
                $(prefix + 'status').html('Сохранено');
                $(prefix + 'status').show();
                invoices_update('/invoice/view/', '#leftm'); 
                $(prefix + 'status').hide(8000);
                get_depts_last('#pay_last');
                // alert("ok");
            },
            error: function () {
                alert('sorry, error'); 
            },
        });
        // clear form
        $(prefix + 'taker').val('')
        $(prefix + 'value').val(0);
        $(prefix + 'comment').val('');
    }
}
// update itype div, 1 from 2
function itype_update(sign) {
    to_page = '/type/view/' + sign +'/';
    up_div = '#uptype' + sign;
    $.get(to_page, function(data) {
            $(up_div).html(data);
        });
}
// add itype
function addtype(sign) {
    input_id = '#add' + sign;
    if ($(input_id).val()) {
        $.ajax({
            url: '/type/add/',
            type: 'POST',
            data: {
                sign : sign,
                name : $(input_id).val(),
            },
            dataType: 'html',
            context: document.body,
            async: true,
            success: function (data) {
                // clear form
                $(input_id).val('');
                // done, update
                itype_update(sign);
                // alert("ok");
            },
            error: function () {
                alert('sorry, error'); 
            },
        });
    } 
    else alert('Пожалуйста проверьте введенные данные.');
}
// save edit itype
function savetype(sign, id) {
    input_id = '#edit' + id;
    if ($(input_id).val()) {
        $.ajax({
            url: '/type/add/',
            type: 'POST',
            data: {
                id: id,
                sign : sign,
                name : $(input_id).val(),
            },
            dataType: 'html',
            context: document.body,
            async: true,
            success: function (data) {
                // done, update
                itype_update(sign);
                // alert("ok");
            },
            error: function () {
                alert('sorry, error'); 
            },
        });
    } 
    else alert('Пожалуйста проверьте введенные данные.');
}
// delete itype
function deltype(sign, id) {
    if (confirm("Уверены, что хотите удалить данные?")) 
    $.get('/type/del/' + id, function(data) {
            itype_update(sign);
        })
        .error(function() { alert("sorry, error"); });
}
// edit itype
function edittype(sign, id) {
    $.get('/type/edit/' + id, function(data) {
            $('#type' + id).html(data);
        })
        .error(function() { alert("sorry, error"); });
}
// update last pays
function get_pay_last(divid)  {
    $.get('/pay/last/', function(data) {
        $(divid).html(data);
    })
    .error(function() { alert("sorry, error"); });
}
// update last transfer
function get_trans_last(divid)  {
    $.get('/transfer/last/', function(data) {
        $(divid).html(data);
    })
    .error(function() { alert("sorry, error"); });
}
// update last depts
function get_depts_last(divid)  {
    $.get('/depts/last/', function(data) {
        $(divid).html(data);
    })
    .error(function() { alert("sorry, error"); });
}
// delete pay
function delpay(id) {
    if (confirm("Уверены, что хотите удалить данные?"))
    $.get('/pay/del/' + id, function(data) {
        invoices_update('/invoice/view/', '#leftm'); 
        get_pay_last('#pay_last');
        // alert("ok");
        })
        .error(function() { alert("sorry, error"); });
}
// delete transfer
function deltrans(id) {
    if (confirm("Уверены, что хотите удалить данные?"))
    $.get('/transfer/del/' + id, function(data) {
        invoices_update('/invoice/view/', '#leftm'); 
        get_trans_last('#pay_last');
        // alert("ok");
        })
        .error(function() { alert("sorry, error"); });
}
// delete dept
function deldepts(id) {
    if (confirm("Уверены, что хотите удалить данные?"))
    $.get('/dept/del/' + id, function(data) {
        invoices_update('/invoice/view/', '#leftm'); 
        get_depts_last('#pay_last');
        // alert("ok");
        })
        .error(function() { alert("sorry, error"); });
}
// update trans select
function update_trans(num, exval, defid) {
    $.ajax({
        url: '/transfer/update/',
        type: 'POST',
        data: {
            val : $('#trans_' + exval).val(),
            form_id : num,
            eventid: exval,
            defaulid: defid
        },
        dataType: 'html',
        context: document.body,
        async: true,
        success: function (data) {
            $('#tr_' + num).html(data);
        },
        error: function () {
            alert('sorry, error'); 
        },
    });
}
// search in operations history
function histsearch() {
    // regexp
    re = /^\d{1,2}(\.)\d{1,2}(\.)\d{2,4}$/;
    // get values
    d1 = $('#date_start').val();
    d2 = $('#date_end').val();
    if (re.test(d1) && re.test(d2)) {
        $.ajax({
            url: '/history/update/',
            type: 'POST',
            data: {
                date_start: d1,
                date_end: d2,
                category: $('input[name|="radiokat"]:checked').val(),
                paytype: $('input[name|="radiopay"]:checked').val(),
                comment: $('#doptext').val(),
            },
            dataType: 'html',
            context: document.body,
            async: true,
            success: function (data) {
                $('#hcontext').html(data);
            },
            error: function () {
                alert('sorry, error'); 
            },
        });
    }
    else alert("Пожалуйста проверьте введенные даты");
}
// change report diapazone
function ch_diapazone() {
    $.ajax({
        url: '/report/diapazone/',
        type: 'GET',
        data: {
            val : $( "#rep_diapazone" ).val(),
            defval: $('#defrepval').val()
        },
        dataType: 'html',
        context: document.body,
        async: true,
        success: function (data) {
            $('#rep_diapvalue').html(data);
        },
        error: function () {
            alert('sorry, error'); 
        },
    });
}
