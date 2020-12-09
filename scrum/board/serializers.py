from datetime import time
from django.contrib.auth import get_user_model
from django.core.siging import TimestampSigner
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.reverse import reverse
from .models import Sprint, Task

User = get_user_model()

class SprintSerializer(serializers.ModelSerializer):
    
    links = serializers.SerializerMethodField('get_links')

    class Meta:
        model = Sprint
        fields = ('id', 'name', 'description', 'end', 'links',)

    def get_links(self, obj):
        req = self.context['request']
        signer = TimestampSigner(settings.WATERCOOLER_SECRET)
        return {
            'self': reverse('sprint-detail', kwargs={'pk':obj.pk}, request=req),
            'tasks': reverse('task-list', request=req) + '?sprint={}'.format(obj.pk),
            'channel': '{proto}://{server}/{channel}'.format(
                proto='wss' if settings.WATERCOOLER_SECURE else 'ws',
                server=settings.WATERCOOLER_SERVER,
                channel=obj.pk
            )
        }

    # def validate_end(self, attrs, source):
    #     end_date = attrs[source]
    #     new = not self.object
    #     changed = self.object and self.object != end_date
    #     if (new or changed) and (end_date < date.today()):
    #         msg = _('End date cannot be in the past.')
    #         raise serializers.ValidateError(msg)
    #     return attrs
    
    # def validate_sprint(self, attrs, source): # Check this function
    #     sprint = attrs[source]
    #     if self.object and self.object.pk:
    #         if sprint != self.object.sprint:
    #             if self.object.statust == Task.STATUS_DONE:
    #                 msg = _('Cannot change the sprint of a completed task.')
    #                 raise serializers.ValidationError(msg)
    #             if sprint and sprint.end < date.today():
    #                 msg = _('Cannot assign tasks to past sprints.')
    #                 raise serializers.ValidationError(msg)
    #     else:
    #         if sprint and sprint.end < date.today():
    #             msg = _('Cannot add tasks to past sprints.')
    #             raise serializers.ValidationError(msg)
    #     return attrs

    # def validate(self, attrs):
    #     sprint = attrs.get('sprint')
    #     status = int(attrs.get('status'))
    #     started = attrs.get('started')
    #     completed = attrs.get('completed')
    #     if not sprint and status != Task.STATUS_TODO:
    #         msg = _('Backlog tasks must have "Not started" status.')
    #         raise serializers.ValidateError(msg)
    #     if started and status == Task.STATUS_TODO:
    #         msg = _('Startted date cannot be set for not started tasks.')
    #         raise serializers.ValidateError(msg)
    #     if completed and status != Task.STATUS_DONE:
    #         msg = _('Completed date cannot be set for uncompleted tasks.')
    #         raise serializers.ValidateError(msg)
        # return attrs

class TaskSerializer(serializers.ModelSerializer):

    assigned = serializers.SlugRelatedField(slug_field=User.USERNAME_FIELD, required=False, read_only=True)
    status_display = serializers.SerializerMethodField('get_status_display')
    links = serializers.SerializerMethodField('get_links')

    class Meta:
        model = Task
        fields = ('id', 'name', 'description', 'sprint', 'status', 'status_display', 
                    'order', 'assigned', 'started', 'due', 'completed', 'links',)
        
    def get_status_display(self, obj):
        return obj.get_status_display()

    def get_links(self, obj):
        req = self.context['request']
        links = {
            'self': reverse('task-detail', kwargs={'pk': obj.pk}, request=req),
            'sprint': None,
            'assigned': None
        }
        if obj.sprint_id:
            links['sprint'] = reverse('sprint-detail', kwargs={'pk': obj.sprint_id}, request=req)
        if obj.assigned:
            links['assigned'] = reverse('user-detail', kwargs={User.USERNAME_FIELD: obj.assigned}, request=req)
        return links

class UserSerializer(serializers.ModelSerializer):
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    links = serializers.SerializerMethodField('get_links')

    class Meta:
        model = User
        fields = ('id', User.USERNAME_FIELD, 'full_name', 'is_active', 'links',)

    def get_links(self, obj):
        req = self.context['request']
        username = obj.get_username()
        return {
            'self': reverse('user-detail', kwargs={User.USERNAME_FIELD: username}, request=req)
        }