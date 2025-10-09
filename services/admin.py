"""
Admin interface for monitoring and analytics services.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

from .models import (
    PerformanceLog, ErrorLog, UserActivityLog, 
    SystemMetrics, AlertLog, AIProcessingMetrics
)


@admin.register(PerformanceLog)
class PerformanceLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'operation', 'duration', 'user', 'correlation_id_short']
    list_filter = ['timestamp', 'operation', 'user']
    search_fields = ['operation', 'correlation_id', 'user__username']
    readonly_fields = ['timestamp', 'correlation_id', 'metadata_display']
    date_hierarchy = 'timestamp'
    
    def correlation_id_short(self, obj):
        return obj.correlation_id[:8] if obj.correlation_id else '-'
    correlation_id_short.short_description = 'Correlation ID'
    
    def metadata_display(self, obj):
        if obj.metadata:
            return format_html('<pre>{}</pre>', json.dumps(obj.metadata, indent=2))
        return '-'
    metadata_display.short_description = 'Metadata'


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'error_type', 'error_message_short', 'user', 'resolved', 'correlation_id_short']
    list_filter = ['timestamp', 'error_type', 'resolved', 'user']
    search_fields = ['error_type', 'error_message', 'correlation_id', 'user__username']
    readonly_fields = ['timestamp', 'correlation_id', 'context_display', 'stack_trace_display']
    date_hierarchy = 'timestamp'
    actions = ['mark_resolved', 'mark_unresolved']
    
    def error_message_short(self, obj):
        return obj.error_message[:50] + '...' if len(obj.error_message) > 50 else obj.error_message
    error_message_short.short_description = 'Error Message'
    
    def correlation_id_short(self, obj):
        return obj.correlation_id[:8] if obj.correlation_id else '-'
    correlation_id_short.short_description = 'Correlation ID'
    
    def context_display(self, obj):
        if obj.context:
            return format_html('<pre>{}</pre>', json.dumps(obj.context, indent=2))
        return '-'
    context_display.short_description = 'Context'
    
    def stack_trace_display(self, obj):
        if obj.stack_trace:
            return format_html('<pre style="max-height: 200px; overflow-y: auto;">{}</pre>', obj.stack_trace)
        return '-'
    stack_trace_display.short_description = 'Stack Trace'
    
    def mark_resolved(self, request, queryset):
        queryset.update(resolved=True)
        self.message_user(request, f'{queryset.count()} errors marked as resolved.')
    mark_resolved.short_description = 'Mark selected errors as resolved'
    
    def mark_unresolved(self, request, queryset):
        queryset.update(resolved=False)
        self.message_user(request, f'{queryset.count()} errors marked as unresolved.')
    mark_unresolved.short_description = 'Mark selected errors as unresolved'


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'activity_type', 'ip_address', 'correlation_id_short']
    list_filter = ['timestamp', 'activity_type', 'user']
    search_fields = ['user__username', 'activity_type', 'correlation_id', 'ip_address']
    readonly_fields = ['timestamp', 'correlation_id', 'metadata_display']
    date_hierarchy = 'timestamp'
    
    def correlation_id_short(self, obj):
        return obj.correlation_id[:8] if obj.correlation_id else '-'
    correlation_id_short.short_description = 'Correlation ID'
    
    def metadata_display(self, obj):
        if obj.metadata:
            return format_html('<pre>{}</pre>', json.dumps(obj.metadata, indent=2))
        return '-'
    metadata_display.short_description = 'Metadata'


@admin.register(AIProcessingMetrics)
class AIProcessingMetricsAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'operation_type', 'content_type', 'processing_time', 'success', 'user', 'cost_estimate']
    list_filter = ['timestamp', 'operation_type', 'content_type', 'success', 'user']
    search_fields = ['operation_type', 'content_type', 'correlation_id', 'user__username']
    readonly_fields = ['timestamp', 'correlation_id']
    date_hierarchy = 'timestamp'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(AlertLog)
class AlertLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'alert_type', 'title', 'severity', 'status', 'acknowledged_by']
    list_filter = ['timestamp', 'alert_type', 'severity', 'status', 'acknowledged_by']
    search_fields = ['alert_type', 'title', 'description', 'correlation_id']
    readonly_fields = ['timestamp', 'correlation_id', 'metadata_display']
    date_hierarchy = 'timestamp'
    actions = ['acknowledge_alerts', 'resolve_alerts', 'close_alerts']
    
    def metadata_display(self, obj):
        if obj.metadata:
            return format_html('<pre>{}</pre>', json.dumps(obj.metadata, indent=2))
        return '-'
    metadata_display.short_description = 'Metadata'
    
    def acknowledge_alerts(self, request, queryset):
        queryset.filter(status='open').update(
            status='acknowledged',
            acknowledged_by=request.user,
            acknowledged_at=timezone.now()
        )
        self.message_user(request, f'{queryset.count()} alerts acknowledged.')
    acknowledge_alerts.short_description = 'Acknowledge selected alerts'
    
    def resolve_alerts(self, request, queryset):
        from django.utils import timezone
        queryset.update(
            status='resolved',
            resolved_at=timezone.now()
        )
        self.message_user(request, f'{queryset.count()} alerts resolved.')
    resolve_alerts.short_description = 'Resolve selected alerts'
    
    def close_alerts(self, request, queryset):
        queryset.update(status='closed')
        self.message_user(request, f'{queryset.count()} alerts closed.')
    close_alerts.short_description = 'Close selected alerts'


@admin.register(SystemMetrics)
class SystemMetricsAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'metric_name', 'metric_value', 'metric_unit']
    list_filter = ['timestamp', 'metric_name', 'metric_unit']
    search_fields = ['metric_name']
    readonly_fields = ['timestamp', 'tags_display']
    date_hierarchy = 'timestamp'
    
    def tags_display(self, obj):
        if obj.tags:
            return format_html('<pre>{}</pre>', json.dumps(obj.tags, indent=2))
        return '-'
    tags_display.short_description = 'Tags'