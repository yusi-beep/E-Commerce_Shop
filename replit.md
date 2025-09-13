# Overview

This is a Django-based e-commerce application for an online shop in Bulgarian. The system provides a complete shopping experience with product catalog, shopping cart functionality, and checkout process. It supports both cash-on-delivery and Stripe credit card payments, with features like coupon codes, image optimization, and multi-format product images (JPEG/WebP/AVIF).

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Enhancements (September 2025)

### Product Descriptions
- Added product description field to Product model with migration
- Integrated descriptions into admin interface and product detail pages
- Modern styled description display with card-based layout

### Modern UI/UX Design
- Upgraded color scheme from green to modern blue accent (#2563eb)
- Enhanced product cards with gradients, shadows, and hover animations
- Improved button styling with elevation effects and transitions
- Better mobile responsiveness across all breakpoints

### Product Variants System
- Complete product variants functionality for size, color, and SKU management
- Admin interface with ProductVariantInline for easy variant management
- Frontend variant selectors with dynamic pricing and stock updates
- Backend cart integration supporting variant-specific pricing and inventory
- Checkout process updated to handle variant orders and stock reduction

### Enhanced Image Gallery
- Improved gallery styling with better hover effects and transitions
- Enhanced mobile responsiveness with horizontal scrolling thumbnails
- Modern card-based gallery presentation with shadows and borders
- Optimized thumbnail sizing and spacing

### Cart System Improvements
- Upgraded cart structure to support product variants
- Dynamic pricing based on selected variant
- Variant information display in cart (size, color, SKU)
- Stock validation per variant during add-to-cart operations

## System Architecture

### Backend Framework
- **Django 5.0+** as the main web framework
- **PostgreSQL** as the primary database (using psycopg2-binary)
- Session-based cart management (no user authentication required)
- Modular app structure with separate concerns

### App Structure
The application is organized into three main Django apps:

1. **Catalog** - Product and category management
   - Handles product listings, categories, and product details
   - Supports multiple product images with modern format optimization
   - Implements slugified URLs for SEO

2. **Cart** - Shopping cart functionality
   - Session-based cart storage (no user login required)
   - Stock validation and quantity management
   - Real-time cart updates with user feedback messages

3. **Checkout** - Order processing and payments
   - Support for both cash-on-delivery and Stripe payments
   - Coupon/discount code system
   - Order status tracking with lifecycle management

### Database Design
- **Product-Category relationship**: Products belong to categories with PROTECT constraint
- **Order-OrderItem structure**: Orders contain multiple items with product references
- **Image optimization**: Automatic WebP/AVIF generation for better performance
- **Flexible pricing**: Support for old_price (sale prices) and BGN/EUR conversion

### Payment Integration
- **Stripe integration** for credit card processing
- **Webhook handling** for payment confirmation
- **Cash-on-delivery** as fallback payment method
- Configurable payment methods through settings

### Image Management
- **Multi-format support**: JPEG, WebP, AVIF for modern browsers
- **Automatic optimization**: Background generation of optimized formats
- **Storage flexibility**: Ready for AWS S3 integration via django-storages
- **Multiple product images**: Up to 5 additional images per product

### Frontend Architecture
- **Server-side rendering** with Django templates
- **Pico CSS framework** for styling
- **Progressive enhancement**: Works without JavaScript
- **Responsive design** with mobile-first approach
- **Modern image formats** with fallback support

## External Dependencies

### Core Framework
- **Django 5.0+** - Web framework
- **Pillow** - Image processing and manipulation
- **psycopg2-binary** - PostgreSQL database adapter

### Payment Processing
- **Stripe** - Credit card payment processing
- **Webhook support** - Real-time payment status updates

### Cloud Storage
- **django-storages** - Abstract storage backends
- **boto3** - AWS SDK for S3 integration

### Database
- **dj-database-url** - Database URL parsing for deployment
- **PostgreSQL** - Primary database system

### Testing
- **pytest** - Testing framework
- **pytest-django** - Django-specific testing utilities

### Optional Enhancements
- **pillow-avif** - AVIF image format support (optional)
- Modern image format generation depends on system libraries

### Email Services
- Configured for transactional emails (order confirmations)
- Ready for SMTP provider integration (SendGrid, etc.)

### Deployment Infrastructure
- **Static file serving** via Django development server or CDN
- **Media file handling** with local storage or S3
- **Environment-based configuration** for different deployment stages