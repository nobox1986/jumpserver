# -*- coding: utf-8 -*-
#
import copy
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from common.utils import validate_ssh_public_key
from common.mixins import BulkSerializerMixin
from common.fields import StringManyToManyField
from common.serializers import AdaptedBulkListSerializer
from common.permissions import CanUpdateDeleteUser
from orgs.mixins.serializers import BulkOrgResourceModelSerializer
from ..models import User, UserGroup


__all__ = [
    'UserSerializer', 'UserPKUpdateSerializer', 'UserUpdateGroupSerializer',
    'UserGroupSerializer', 'UserGroupListSerializer',
    'UserGroupUpdateMemberSerializer', 'ChangeUserPasswordSerializer',
    'ResetOTPSerializer',
]


class UserSerializer(BulkSerializerMixin, serializers.ModelSerializer):

    can_update = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()

    class Meta:
        model = User
        list_serializer_class = AdaptedBulkListSerializer
        fields = [
            'id', 'name', 'username', 'password', 'email', 'public_key',
            'groups',  'groups_display',
            'role', 'role_display',  'wechat', 'phone', 'otp_level',
            'comment', 'source', 'source_display', 'is_valid', 'is_expired',
            'is_active', 'created_by', 'is_first_login',
            'date_password_last_updated', 'date_expired', 'avatar_url',
            'can_update', 'can_delete',
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False, 'allow_null': True, 'allow_blank': True},
            'public_key': {'write_only': True},
            'groups_display': {'label': _('Groups name')},
            'source_display': {'label': _('Source name')},
            'is_first_login': {'label': _('Is first login'), 'read_only': True},
            'role_display': {'label': _('Role name')},
            'is_valid': {'label': _('Is valid')},
            'is_expired': {'label': _('Is expired')},
            'avatar_url': {'label': _('Avatar url')},
            'source': {'read_only': True},
            'created_by': {'read_only': True, 'allow_blank': True},
            'can_update': {'read_only': True},
            'can_delete': {'read_only': True},
        }

    def get_can_update(self, obj):
        return CanUpdateDeleteUser.has_update_object_permission(
            self.context['request'], self.context['view'], obj
        )

    def get_can_delete(self, obj):
        return CanUpdateDeleteUser.has_delete_object_permission(
            self.context['request'], self.context['view'], obj
        )

    def validate_role(self, value):
        request = self.context.get('request')
        if not request.user.is_superuser and value != User.ROLE_USER:
            role_display = dict(User.ROLE_CHOICES)[User.ROLE_USER]
            msg = _("Role limit to {}".format(role_display))
            raise serializers.ValidationError(msg)
        return value

    def validate_password(self, password):
        from ..utils import check_password_rules
        password_strategy = self.initial_data.get('password_strategy')
        if password_strategy == '0':
            return
        if password_strategy is None and not password:
            return
        if not check_password_rules(password):
            msg = _('Password does not match security rules')
            raise serializers.ValidationError(msg)
        return password

    def validate_groups(self, groups):
        role = self.initial_data.get('role')
        if self.instance:
            role = role or self.instance.role
        if role == User.ROLE_AUDITOR:
            return []
        return groups

    @staticmethod
    def change_password_to_raw(attrs):
        password = attrs.pop('password', None)
        if password:
            attrs['password_raw'] = password
        return attrs

    def validate(self, attrs):
        attrs = self.change_password_to_raw(attrs)
        return attrs


class UserPKUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'public_key']

    @staticmethod
    def validate_public_key(value):
        if not validate_ssh_public_key(value):
            raise serializers.ValidationError(_('Not a valid ssh public key'))
        return value


class UserUpdateGroupSerializer(serializers.ModelSerializer):
    groups = serializers.PrimaryKeyRelatedField(many=True, queryset=UserGroup.objects.all())

    class Meta:
        model = User
        fields = ['id', 'groups']


class UserGroupSerializer(BulkOrgResourceModelSerializer):
    users = serializers.PrimaryKeyRelatedField(
        required=False, many=True, queryset=User.objects.all(), label=_('User')
    )

    class Meta:
        model = UserGroup
        list_serializer_class = AdaptedBulkListSerializer
        fields = [
            'id', 'name',  'users', 'comment', 'date_created',
            'created_by',
        ]
        extra_kwargs = {
            'created_by': {'label': _('Created by'), 'read_only': True}
        }

    def validate_users(self, users):
        for user in users:
            if user.is_super_auditor:
                msg = _('Auditors cannot be join in the user group')
                raise serializers.ValidationError(msg)
        return users


class UserGroupListSerializer(UserGroupSerializer):
    users = StringManyToManyField(many=True, read_only=True)


class UserGroupUpdateMemberSerializer(serializers.ModelSerializer):
    users = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())

    class Meta:
        model = UserGroup
        fields = ['id', 'users']


class ChangeUserPasswordSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['password']


class ResetOTPSerializer(serializers.Serializer):
    msg = serializers.CharField(read_only=True)
