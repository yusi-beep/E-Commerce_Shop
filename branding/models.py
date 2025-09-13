import os
from PIL import Image
from io import BytesIO
from django.db import models
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.utils.html import format_html


def validate_image_size(value):
    """Validate that the uploaded image meets size requirements."""
    if value:
        if hasattr(value, 'temporary_file_path'):
            # For uploaded files
            path = value.temporary_file_path()
            with Image.open(path) as img:
                width, height = img.size
        else:
            # For in-memory files
            with Image.open(value) as img:
                width, height = img.size
        
        if width > 512 or height > 512:
            raise ValidationError('Image dimensions must not exceed 512×512 pixels.')


def validate_logo_file_size(value):
    """Validate logo file size (max 512KB)."""
    if value and hasattr(value, 'size') and value.size > 512 * 1024:  # 512KB
        raise ValidationError('Logo file size must not exceed 512KB.')


def validate_favicon_file_size(value):
    """Validate favicon file size (max 256KB)."""
    if value and hasattr(value, 'size') and value.size > 256 * 1024:  # 256KB
        raise ValidationError('Favicon file size must not exceed 256KB.')


class SiteBranding(models.Model):
    """
    Site branding configuration - singleton model.
    Only one instance should exist at any time.
    """
    # Logo settings
    logo = models.ImageField(
        upload_to='branding/logos/', 
        blank=True, 
        null=True,
        validators=[validate_logo_file_size, validate_image_size],
        help_text="Upload site logo (SVG/PNG preferred, max 512KB, max 512×512px)"
    )
    logo_alt_text = models.CharField(
        max_length=200, 
        default="Site Logo",
        help_text="Alt text for accessibility and SEO"
    )
    logo_max_width = models.PositiveIntegerField(
        default=200,
        help_text="Maximum width for logo display (pixels)"
    )
    logo_link_target = models.CharField(
        max_length=200,
        default="/",
        help_text="URL where logo click should navigate"
    )
    
    # Favicon settings
    favicon = models.ImageField(
        upload_to='branding/favicons/',
        blank=True,
        null=True,
        validators=[validate_favicon_file_size],
        help_text="Upload favicon (ICO/PNG/SVG, max 256KB)"
    )
    
    # Generated favicon variants (auto-populated)
    favicon_ico = models.FileField(upload_to='branding/favicons/', blank=True, null=True, editable=False)
    favicon_svg = models.FileField(upload_to='branding/favicons/', blank=True, null=True, editable=False)
    favicon_32 = models.ImageField(upload_to='branding/favicons/', blank=True, null=True, editable=False)
    favicon_16 = models.ImageField(upload_to='branding/favicons/', blank=True, null=True, editable=False)
    apple_touch_icon = models.ImageField(upload_to='branding/favicons/', blank=True, null=True, editable=False)
    
    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Site Branding"
        verbose_name_plural = "Site Branding"
    
    def __str__(self):
        return "Site Branding Configuration"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists (singleton)
        if not self.pk and SiteBranding.objects.exists():
            raise ValidationError('Only one branding configuration is allowed.')
        
        super().save(*args, **kwargs)
        
        # Generate favicon variants after saving
        if self.favicon:
            self._generate_favicon_variants()
    
    def _generate_favicon_variants(self):
        """Generate favicon variants from the uploaded favicon."""
        if not self.favicon:
            return
        
        try:
            with Image.open(self.favicon.path) as img:
                # Convert to RGBA if not already
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Generate 32x32 PNG
                favicon_32 = img.resize((32, 32), Image.Resampling.LANCZOS)
                favicon_32_io = BytesIO()
                favicon_32.save(favicon_32_io, format='PNG')
                favicon_32_io.seek(0)
                self.favicon_32.save(
                    'favicon-32x32.png',
                    ContentFile(favicon_32_io.getvalue()),
                    save=False
                )
                
                # Generate 16x16 PNG
                favicon_16 = img.resize((16, 16), Image.Resampling.LANCZOS)
                favicon_16_io = BytesIO()
                favicon_16.save(favicon_16_io, format='PNG')
                favicon_16_io.seek(0)
                self.favicon_16.save(
                    'favicon-16x16.png',
                    ContentFile(favicon_16_io.getvalue()),
                    save=False
                )
                
                # Generate Apple Touch Icon (180x180)
                apple_icon = img.resize((180, 180), Image.Resampling.LANCZOS)
                apple_icon_io = BytesIO()
                apple_icon.save(apple_icon_io, format='PNG')
                apple_icon_io.seek(0)
                self.apple_touch_icon.save(
                    'apple-touch-icon.png',
                    ContentFile(apple_icon_io.getvalue()),
                    save=False
                )
                
                # Generate ICO file (16x16 and 32x32 combined)
                ico_sizes = [(16, 16), (32, 32)]
                ico_images = []
                for size in ico_sizes:
                    resized = img.resize(size, Image.Resampling.LANCZOS)
                    ico_images.append(resized)
                
                ico_io = BytesIO()
                ico_images[0].save(
                    ico_io, 
                    format='ICO', 
                    sizes=ico_sizes,
                    append_images=ico_images[1:]
                )
                ico_io.seek(0)
                self.favicon_ico.save(
                    'favicon.ico',
                    ContentFile(ico_io.getvalue()),
                    save=False
                )
                
                # Save the model with new variants
                super().save(update_fields=[
                    'favicon_32', 'favicon_16', 'apple_touch_icon', 'favicon_ico'
                ])
                
        except Exception as e:
            # Log error but don't fail the save
            print(f"Error generating favicon variants: {e}")
    
    @classmethod
    def get_current(cls):
        """Get or create the singleton branding instance."""
        instance, created = cls.objects.get_or_create(
            pk=1,  # Force primary key to be 1
            defaults={
                'logo_alt_text': 'Site Logo',
                'logo_max_width': 200,
                'logo_link_target': '/',
            }
        )
        return instance
    
    def get_favicon_html_tags(self):
        """Generate HTML tags for favicon variants."""
        tags = []
        
        if self.favicon_ico:
            tags.append(f'<link rel="icon" type="image/x-icon" href="{self.favicon_ico.url}">')
        
        if self.favicon_svg and self.favicon.name.endswith('.svg'):
            tags.append(f'<link rel="icon" type="image/svg+xml" href="{self.favicon.url}">')
        
        if self.favicon_32:
            tags.append(f'<link rel="icon" type="image/png" sizes="32x32" href="{self.favicon_32.url}">')
        
        if self.favicon_16:
            tags.append(f'<link rel="icon" type="image/png" sizes="16x16" href="{self.favicon_16.url}">')
        
        if self.apple_touch_icon:
            tags.append(f'<link rel="apple-touch-icon" href="{self.apple_touch_icon.url}">')
        
        return format_html('\n'.join(tags))
