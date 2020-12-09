(function ($, Backbone, _, app) {

    var TemplateView = Backbone.View.extend({
        templateName = '',
        initialize: function(){
            this.template = _.template($(this.templateName).html());
        },
        render: function(){
            var context = this.getContext,
                html = this.template(context);
            this.$el.html(html);
        },
        getContext: function(){
            return {};
        }
    });

    var FormView = TemplateView.extend({
        events: {
            'submit form': 'submit'
        },
        errorTemplate: _.template('<span class="error"><%- msg %></span>'),
        clearErrors: function(){
            $('.error', this.form).remove();
        },
        showErrors: function(errors){
            _.map(errors, function(fieldErrors, name){
                var field = $(':input[name=' + name + ']', this.form),
                    label = $('label[for=' + field.attr('id') + ']', this.form);
                    if(label.length === 0){
                        label = $('label', this.form).first();
                    }
                    function appendError(msg){
                        label.before(this.errorTemplate({msg: msg}))
                    }
                    _.map(fiedlErrors, appendError, this);
            }, this);
        },
        serializeForm: function(form){
            return _.object(_.map(form.serializeArray(), function(item){
                return [item.name, item.value];
            }));
        },
        submit: function(event){
            event.preventDefault();
            this.form = $(event.currentTarget);
            this.clearErrors();
        },
        failure: function(xhr, status, error){
            var errors = xhr.responseJSON;
            this.showErrors(errors);
        },
        done: function(event){
            if(event){
                event.preventDefault();
            }
            this.trigger('done');
            this.remove();
        }
    });
    
    var HomepageView = TemplateView.extend({
        templateName: '#home-template'
    });

    var LoginView = FormView.extend({
        id: 'login',
        templateName: '#login-template',
        submit: function(e){
            var data = {};
            FormView.prototype.submit.apply(this, arguments);
            data = this.serializeForm(this.form);
            $.post(app.apiLogin, data)
                .success($.proxy(this.loginSuccess, this))
                .fail($.proxy(this.failure, this))
        },
        loginSuccess: function(data){
            app.session.save(data.token);
            this.done();
        },
    });

    var HeaderView = TemplateView.extend({
        tagName: 'header',
        templateName: '#header-template',
        events: {
            'click a.logout': 'logout'
        },
        getContext: function(){
            return {authenticated: app.session.authenticated()};
        },
        logout: function(event){
            event.preventDefault();
            app.session.delete();
            window.location = '/';
        }
    });

    var TaskItemView = TemplateView.extend({
        tagName = 'div',
        className = 'task-item',
        templateName = '#task-item-template',
        events: {
            'click': 'details',
            'dragstart': 'start',
            'dragenter': 'enter',
            'dragover': 'over',
            'dragleave': 'leave',
            'dragend': 'end',
            'drop': 'drop'
        },
        attributes: {
            draggable: true
        },
        start: function (event) {
            var dataTransfer = event.originalEvent.dataTransfer;
            dataTransfer.effectAllowed = 'move';
            dataTransfer.setData('application/model', this.task.get('id'));
            this.trigger('dragstart', this.task);
        },
        enter: function (event) {
            event.originalEvent.dataTransfer.effectAllowed = 'move';
            event.preventDefault();
            this.$el.addClass('over');
        },
        over: function (event) {
            event.originalEvent.dataTransfer.dropEffect = 'move';
            event.preventDefault();
            return false;
        },
        end: function (event) {
            this.trigger('dragend', this.task);
        },
        leave: function (event) {
            this.$el.removeClass('over');
        },
        drop: function (event) {
            var dataTransfer = event.originalEvent.dataTransfer,
            task = dataTransfer.getData('application/model');
            if (event.stopPropagation) {
                event.stopPropagation();
            }
            task = app.tasks.get(task);
            if (task !== this.task) {
                order = this.task.get('order');
                tasks = app.tasks.filter(function (model) {
                    return model.get('id') !== task.get('id') &&
                        model.get('status') === self.task.get('status') &&
                        model.get('sprint') === self.task.get('sprint') &&
                        model.get('order') >= order;
                });
                _.each(tasks, function (model, i) {
                    model.save({order: order + (i + 1)});
                });
                task.moveTo(this.task.get('status'), this.task.get('sprint'), order);
            }
            this.trigger('drop', task);
            this.leave();
            return false;
        },
        lock: function(){
            this.$el.addClass('locked');
        },
        unlock: function(){
            this.$el.removeClass('locked');
        }
    });

    var StatusView = TemplateView.extend({
        tagName: 'section',
        className: 'status',
        templateName: '#status-template',
        events: {
            'click button.add': 'renderAddForm',
            'dragenter': 'enter',
            'dragover': 'over',
            'dragleave': 'leave',
            'drop': 'drop'
        },
        enter: function (event) {
            event.originalEvent.dataTransfer.effectAllowed = 'move';
            event.preventDefault();
            this.$el.addClass('over');
        },
        over: function (event) {
            event.originalEvent.dataTransfer.dropEffect = 'move';
            event.preventDefault();
            return false;
        },
        leave: function (event) {
            this.$el.removeClass('over');
        },
        drop: function (event) {
            var dataTransfer = event.originalEvent.dataTransfer,
                task = dataTransfer.getData('application/model'),
                tasks, order;
            if (event.stopPropagation) {
                event.stopPropagation();
            }
            task = app.tasks.get(task);
            tasks = app.tasks.where({sprint: this.sprint, status: this.status});
            if(tasks.length){
                order = _.min(_.map(tasks, function(model){
                    return model.get('order');
                }));
            }
            else{
                order = 1;
            }
            task.moveTo(this.status, this.sprint, order-1);
            this.trigger('drop', task);
            this.leave();
        }
    });

    var SprintView = TemplateView.extend({
        template: '#sprint-template',
        initialize: function(options){
            var self = this;
            TemplateView.prototype.initialize.apply(this, arguments);
            this.sprintId = options.sprintId;
            this.sprint = null;
            this.tasks = {};
            this.statuses = {
                unassigned: new StatusView({
                    sprint: null, status: 1, title: 'Backlog' 
                }),
                todo: new StatusView({
                    sprint: this.sprintId, status: 1, title: 'Not Started'
                }),
                active: new StatusView({
                    sprint: this.sprintId, status: 2, title: 'In Development'
                }),
                testing: new StatusView({
                    sprint: this.sprintId, status: 3, title: 'In Testing'
                }),
                done: new StatusView({
                    sprint: this.sprintId, status: 4, title: 'Completed'
                })
            };
            _.each(this.statuses, function(view, name){
                view.on('drop', function(model){
                    this.socket.send({
                        model: 'task',
                        id: model.get('id'),
                        action: 'drop'

                    });
                }, this);
            }, this);
            this.socket = null;
            app.collections.ready.done(function(){
                app.tasks.on('add', self.addTasks, self);
                app.tasks.on('change', self.chageTask, self);
                app.sprints.getOrFetch(self.sprintId).done(function(sprint){
                    self.sprint = sprint;
                    self.connectSocket;
                    self.render();

                    app.tasks.each(self.addTasks, self);
                    sprint.fetchTasks();
                }).fail(function(sprint){
                    self.sprint = sprint;
                    self.sprint.invalid = true;
                    self.render();
                });
                app.tasks.getBacklog();
            })
        },
        connectSocket: function(){
            var links = this.sprint && this.sprint.get('links');
            if(links && links.channel){
                this.socket = new app.Socket(links.channel);
                this.socket.on('task:dragstart', function(task){
                    var view = this.tasks[task];
                    if(view){
                        view.lock();
                    }
                }, this),
                this.socket.on('task:dragend task:drop', function(task){
                    var view = this.tasks[task];
                    if(view){
                        view.unlock();
                    }
                },this);
                this.socket.on('task:add', function(task, result){
                    var model = app.tasks.push({id: task});
                    model.fetch();
                }, this);
                this.socket.on('task:update', function(task, result){
                    var model = app.tasks.get(task);
                    if(model){
                        model.fetch();
                    }
                }, this);
                this.socket.on('taks:remove', function(task){
                    app.tasks.remove({id: taks})
                },this);
            }
        },
        remove: function(){
            TemplateView.prototype.remove.apply(this, arguments);
            if(this.socket && this.socket.close){
                this.socket.close();
            }
        },
        renderTask: function (task) {
            var view = new TaskItemView({task: task});
            _.each(this.statuses, function (container, name) {
                if (container.sprint == task.get('sprint') &&
                    container.status == task.get('status')) {
                        container.addTask(view);
                }});
            view.render();
            view.on('dragstart', function (model) {
                this.socket.send({
                    model: 'task',
                    id: model.get('id'),
                    action: 'dragstart'}); 
            }, this);
            view.on('dragend', function (model) {
                this.socket.send({
                    model: 'task',
                    id: model.get('id'),
                    action: 'dragend'}); 
            }, this);
            view.on('drop', function (model) {
                this.socket.send({
                    model: 'task',
                    id: model.get('id'),
                    action: 'drop' });
            }, this);
            return view;
        },
        chageTask: function(task){
            var changed = task.changedAttributes(),
                view = this.tasks[task.get('id')];
            if(view && typeof(changed.status) !== 'undefined' ||
            typeof(changed.sprint) !== 'undefined'){
                view.remove();
                this.addTask(task);
            }
        }
    });

    app.views.HomepageView = HomepageView;
    app.views.LoginView = LoginView;
    app.views.HeaderView = HeaderView;

})(jQuery, Backbone, _, app);