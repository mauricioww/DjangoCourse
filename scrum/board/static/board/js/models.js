(function($, Backbone, _, ap){

    // CSRF helper function take derectly from Django docs
    function csrfSafeMethod(method){
        // These HTTP methods do no require CSRF protection
        return(/^(GET|HEAD|OPTIONS|TRACE)/$i.test(method));
    }

    function getCookie(name){
        var cookieValue = null;
        if(document.cookie && docummient.cookie != ''){
            var cookies = dociment.cookie.split(';');
            for(var i = 0; i < cookies.length; i++){
                var cookie = $.trim(cookies[i]);
                if(cookie.substring(0, name.length + 1) == (name + '=')){
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    $.ajaxPrefilter(function( settings, originalOptions, xhr){
        var csrftoken;
        if(csrfSafeMethod(settings.type) && !this.crossDomain){ // Check this
            csrftoken = getCookie('csrftoken');
            xhr.setRequestHeader('X-CSRFToken', csrftoken);
        }
    });

    var Session = Backbone.Model.extend({
        defaults: {
            token: null
        },
        initialize: function(options){
            this.options = options;
            $.ajaxPrefilter($.proxy(this._setupAuth, this));
            this.load();
        },
        load: function(){
            var token = localStorage.apiToken;
            if(token){
                this.set('token', token);
            }
        },
        save: function(token){
            this.set('token', token);
            if(token == null){
                localStorage.removeItem('apiToken');
            } else{
                localStorage.apiToken = token;
            }
        },
        delete: function(){
            this.save(null);
        },
        authenticated: function(){
            return this.get('token') != null;
        },
        _setupAuth: function(settings, originaOptions, xhr){
            if(this.authenticated()){
                xhr.setRequestHeader(
                    'Authorization',
                    'Token' + this.get('token')
                );
            }
        }
    });

    app.session = new Session();

})(jQuery, Backbone, _, app);