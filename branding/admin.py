from django.contrib import admin
from django.utils.html import format_html
from .models import SiteBranding


@admin.register(SiteBranding)
class SiteBrandingAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Logo Settings', {
            'fields': ('logo', 'logo_preview', 'logo_alt_text', 'logo_max_width', 'logo_link_target'),
            'description': 'Configure your site logo and its display settings.'
        }),
        ('Favicon Settings', {
            'fields': ('favicon', 'favicon_preview'),
            'description': 'Upload a favicon. Multiple formats will be generated automatically.'
        }),
        ('Generated Variants', {
            'fields': ('favicon_variants_display',),
            'description': 'Auto-generated favicon variants for different devices and browsers.',
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('logo_preview', 'favicon_preview', 'favicon_variants_display')
    
    def has_add_permission(self, request):
        # Only allow one branding configuration
        if SiteBranding.objects.exists():
            return False
        return super().has_add_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of branding configuration
        return False
    
    def logo_preview(self, obj):
        """Show logo preview in admin."""
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 100px; border: 1px solid #ddd; padding: 5px;" alt="Logo Preview">',
                obj.logo.url
            )
        return "No logo uploaded"
    logo_preview.short_description = "Logo Preview"
    
    def favicon_preview(self, obj):
        """Show favicon preview in admin."""
        if obj.favicon:
            return format_html(
                '<img src="{}" style="width: 32px; height: 32px; border: 1px solid #ddd; padding: 2px;" alt="Favicon Preview">',
                obj.favicon.url
            )
        return "No favicon uploaded"
    favicon_preview.short_description = "Favicon Preview"
    
    def favicon_variants_display(self, obj):
        """Show generated favicon variants."""
        variants = []
        
        if obj.favicon_ico:
            variants.append(f'<div><strong>ICO:</strong> <a href="{obj.favicon_ico.url}" target="_blank">favicon.ico</a></div>')
        
        if obj.favicon_32:
            variants.append(f'<div><strong>32×32 PNG:</strong> <a href="{obj.favicon_32.url}" target="_blank">favicon-32x32.png</a></div>')
        
        if obj.favicon_16:
            variants.append(f'<div><strong>16×16 PNG:</strong> <a href="{obj.favicon_16.url}" target="_blank">favicon-16x16.png</a></div>')
        
        if obj.apple_touch_icon:
            variants.append(f'<div><strong>Apple Touch Icon:</strong> <a href="{obj.apple_touch_icon.url}" target="_blank">apple-touch-icon.png</a></div>')
        
        if variants:
            return format_html('<div style="line-height: 1.5;">{}</div>'.format(''.join(variants)))
        
        return "No variants generated yet. Upload a favicon to generate them automatically."
    favicon_variants_display.short_description = "Generated Variants"
    
    def changelist_view(self, request, extra_context=None):
        # Redirect to edit page if branding exists, create page if not
        if SiteBranding.objects.exists():
            branding = SiteBranding.objects.first()
            from django.shortcuts import redirect
            return redirect('admin:branding_sitebranding_change', branding.pk)
        return super().changelist_view(request, extra_context)
    
    class Media:
        css = {
            'all': ('admin/css/widgets.css',)
        }
