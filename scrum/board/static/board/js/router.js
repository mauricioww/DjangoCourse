(function($, Backbone, _, app){
    var AppRoute = Backbone.Router.extend({
        routes: {
            '': 'home'
        },
        initialize: function(options){
            this.contentElement = '#content';
            this.current = null;
            Backbone.history.start();
        },
        home: function(){
            var view = new app.views.HomepageView({el: this.contentElement});
            this.render(view)
        },
        render: function(view){
            if(this.current){
                this.current.$el = $();
                this.current.remove();
            }
            this.current = view;
            this.current.render();
        }
    });

    app.router = AppRoute;

})(jQuery, Backbone, _, app);