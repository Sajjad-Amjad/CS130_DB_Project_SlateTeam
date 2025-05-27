# Complete Slate API Testing Guide - Start to End

## 🚀 Overview

This comprehensive guide covers testing the **Slate API** - a freelancing platform, built with FastAPI and SQL Server. The guide includes Swagger UI testing testing, and complete workflow examples with test data.

---

## 📋 Table of Contents

1. [Pre-Testing Setup](#pre-testing-setup)
2. [Manual Testing with Swagger UI](#manual-testing-with-swagger-ui)
3. [Complete API Workflow Examples](#complete-api-workflow-examples)

---

## 🛠️ Pre-Testing Setup

### 1. Start the API Server

```bash
cd backend
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate     # On Windows
python run.py
```

**Expected Output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 2. Verify Database Connection

**Quick Health Check:**
```bash
curl http://127.0.0.1:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy"
}
```

### 3. Access Swagger UI

Open browser: **http://127.0.0.1:8000/docs**

---

## 🧪 Manual Testing with Swagger UI

### Step 1: Health Check

**Endpoint:** `GET /health`

**Steps:**
1. Click "Try it out" → "Execute"

**Expected Response:**
```json
{
  "status": "healthy"
}
```

### Step 2: Register Users

#### Register Seller (Sajjad)

**Endpoint:** `POST /api/auth/register`

**Request Body:**
```json
{
  "email": "sajjad.dev@gmail.com",
  "password": "sajjad123456",
  "user_role": "seller",
  "full_name": "Sajjad Amjad",
  "country": "Pakistan",
  "language": "Urdu"
}
```

**Expected Response (200):**
```json
{
  "user_id": 5,
  "email": "sajjad.dev@gmail.com",
  "full_name": "Sajjad Amjad",
  "user_role": "seller",
  "country": "Pakistan",
  "language": "Urdu",
  "profile_picture": null,
  "registration_date": "2025-05-27T11:45:18.408000",
  "is_active": true,
  "last_login": null
}
```

#### Register Buyer (Ahmed)

**Endpoint:** `POST /api/auth/register`

**Request Body:**
```json
{
  "email": "ahmed.buyer@gmail.com",
  "password": "ahmed123456",
  "user_role": "buyer",
  "full_name": "Ahmed Hassan",
  "country": "Pakistan",
  "language": "Urdu"
}
```

**Expected Response (200):**
```json
{
  "user_id": 6,
  "email": "ahmed.buyer@gmail.com",
  "full_name": "Ahmed Hassan",
  "user_role": "buyer",
  "country": "Pakistan",
  "language": "Urdu",
  "profile_picture": null,
  "registration_date": "2025-05-27T11:45:19.421000",
  "is_active": true,
  "last_login": null
}
```

### Step 3: Login and Get Access Tokens

#### Login Seller

**Endpoint:** `POST /api/auth/token`

**Request (Form Data):**
```
username: sajjad.dev@gmail.com
password: sajjad123456
```

**Expected Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1IiwiZXhwIjoxNzQ4MzQ4MTIwfQ.koLuir3vnfS8f4ewxK2boFU5mBJJIfr3YyjlCd6FgHw",
  "token_type": "bearer"
}
```

**🔑 IMPORTANT:** Copy the `access_token` value for authentication.

#### Set Authorization in Swagger

1. Click **"Authorize"** button (🔒 icon) at top of Swagger UI
2. Enter: `Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (your actual token)
3. Click "Authorize"

### Step 4: Create Seller Profile

**Endpoint:** `POST /api/users/seller-profile`

**Request Body:**
```json
{
  "professional_title": "Full-Stack Developer & WordPress Expert",
  "description": "Experienced Pakistani developer specializing in modern web applications. I create responsive websites, e-commerce solutions, and custom web applications using React, Node.js, Python, and WordPress. Fluent in Urdu and English, I understand local Pakistani business needs and deliver high-quality solutions on time.",
  "portfolio_links": {
    "website": "https://sajjaddev.pk",
    "github": "https://github.com/sajjadamjad",
    "linkedin": "https://linkedin.com/in/sajjadamjad"
  },
  "education": "Bachelor's in Computer Science from COMSATS University Islamabad",
  "certifications": "AWS Certified Developer, Google Cloud Professional, Meta React Certificate",
  "languages": ["Urdu", "English", "Punjabi"],
  "personal_website": "https://sajjaddev.pk",
  "social_media_links": {
    "linkedin": "https://linkedin.com/in/sajjadamjad",
    "twitter": "https://twitter.com/sajjadamjad",
    "instagram": "https://instagram.com/sajjaddev"
  }
}
```

**Expected Response (200):**
```json
{
  "professional_title": "Full-Stack Developer & WordPress Expert",
  "description": "Experienced Pakistani developer...",
  "portfolio_links": {
    "website": "https://sajjaddev.pk",
    "github": "https://github.com/sajjadamjad",
    "linkedin": "https://linkedin.com/in/sajjadamjad"
  },
  "education": "Bachelor's in Computer Science from COMSATS University Islamabad",
  "certifications": "AWS Certified Developer, Google Cloud Professional, Meta React Certificate",
  "languages": ["Urdu", "English", "Punjabi"],
  "personal_website": "https://sajjaddev.pk",
  "social_media_links": {
    "linkedin": "https://linkedin.com/in/sajjadamjad",
    "twitter": "https://twitter.com/sajjadamjad",
    "instagram": "https://instagram.com/sajjaddev"
  },
  "seller_id": 2,
  "user_id": 5,
  "response_time": null,
  "completion_rate": null,
  "rating_average": null,
  "total_earnings": null,
  "account_level": "new",
  "created_at": "2025-05-27T11:45:22.887000",
  "updated_at": "2025-05-27T11:45:22.887000"
}
```

### Step 5: Get Categories

**Endpoint:** `GET /api/categories/`

**Expected Response (200):**
```json
[
  {
    "name": "Graphics & Design",
    "description": "Logo design, web design, and more",
    "icon": "design-icon",
    "display_order": 1,
    "category_id": 1,
    "parent_category_id": null,
    "is_active": true
  },
  {
    "name": "Programming & Tech",
    "description": "Web development, mobile apps, and more",
    "icon": "programming-icon",
    "display_order": 5,
    "category_id": 5,
    "parent_category_id": null,
    "is_active": true
  },
  {
    "name": "Web Development",
    "description": "Frontend and backend development",
    "icon": null,
    "display_order": 1,
    "category_id": 9,
    "parent_category_id": 5,
    "is_active": true
  }
]
```

### Step 6: Create a Gig

**Endpoint:** `POST /api/gigs/`

**Request Body:**
```json
{
  "title": "I will develop a professional WordPress website for Pakistani businesses",
  "description": "🇵🇰 Pakistani Developer - Expert WordPress Solutions\n\n✅ What You Get:\n• Custom WordPress website design\n• Mobile-responsive layout\n• SEO optimization for Pakistani market\n• Urdu/English language support\n• Contact forms and business integration\n• Payment gateway setup (JazzCash, EasyPaisa, Bank transfers)\n• Google My Business optimization\n• Social media integration\n\n✅ Why Choose Me:\n• 5+ years experience with Pakistani businesses\n• Understanding of local market needs\n• Fluent in Urdu and English\n• Available during Pakistani business hours (PKT)\n• Post-launch support included\n\n✅ Perfect For:\n• Small businesses in Pakistan\n• E-commerce stores\n• Service-based companies\n• Restaurants and local shops\n• Professional portfolios\n\nI understand Pakistani business culture and will create a website that resonates with your local audience while meeting international standards.",
  "category_id": 5,
  "subcategory_id": 9,
  "gig_metadata": {
    "target_market": "Pakistan",
    "languages_supported": ["Urdu", "English"],
    "business_types": ["Small Business", "E-commerce", "Services", "Restaurants"],
    "payment_gateways": ["JazzCash", "EasyPaisa", "Bank Transfer"],
    "tech_stack": ["WordPress", "Elementor", "WooCommerce", "PHP", "MySQL"]
  },
  "search_tags": "wordpress, pakistan, urdu, website, business, ecommerce, jazzcash, easypaisa, islamabad, karachi, lahore",
  "requirements": "Please provide:\n1. Your business details and requirements\n2. Preferred color scheme and style\n3. Logo and brand assets (if available)\n4. Content for the website (text, images)\n5. Any specific Pakistani payment methods needed\n6. Reference websites you like\n7. Timeline preferences",
  "faqs": {
    "Do you work with Pakistani payment gateways?": "Yes! I specialize in integrating JazzCash, EasyPaisa, and local bank payment systems.",
    "Can you add Urdu language support?": "Absolutely! I can create bilingual websites with Urdu and English support.",
    "Do you understand Pakistani business needs?": "Yes, I'm a Pakistani developer with 5+ years of experience working with local businesses."
  }
}
```

**Expected Response (200):**
```json
{
  "title": "I will develop a professional WordPress website for Pakistani businesses",
  "description": "🇵🇰 Pakistani Developer - Expert WordPress Solutions...",
  "category_id": 5,
  "subcategory_id": 9,
  "gig_metadata": {
    "target_market": "Pakistan",
    "languages_supported": ["Urdu", "English"],
    "business_types": ["Small Business", "E-commerce", "Services", "Restaurants"],
    "payment_gateways": ["JazzCash", "EasyPaisa", "Bank Transfer"],
    "tech_stack": ["WordPress", "Elementor", "WooCommerce", "PHP", "MySQL"]
  },
  "search_tags": "wordpress, pakistan, urdu, website, business, ecommerce, jazzcash, easypaisa, islamabad, karachi, lahore",
  "requirements": "Please provide:\n1. Your business details and requirements...",
  "faqs": {
    "Do you work with Pakistani payment gateways?": "Yes! I specialize in integrating JazzCash, EasyPaisa, and local bank payment systems.",
    "Can you add Urdu language support?": "Absolutely! I can create bilingual websites with Urdu and English support."
  },
  "gig_id": 2,
  "seller_id": 2,
  "is_featured": false,
  "is_active": true,
  "impression_count": 0,
  "click_count": 0,
  "conversion_rate": null,
  "avg_response_time": null,
  "total_orders": 0,
  "total_reviews": 0,
  "ranking_score": 0.0,
  "created_at": "2025-05-27T11:45:24.983000",
  "updated_at": "2025-05-27T11:45:24.983000"
}
```

### Step 7: Create Gig Packages

#### Standard Package

**Endpoint:** `POST /api/gigs/2/packages`

**Request Body:**
```json
{
  "package_type": "standard",
  "title": "Professional Business Website + E-commerce",
  "description": "Complete solution for Pakistani businesses wanting online sales",
  "price": 35000,
  "delivery_time": 10,
  "revision_count": 3,
  "features": {
    "pages": 10,
    "responsive_design": true,
    "advanced_seo": true,
    "contact_forms": true,
    "urdu_english_bilingual": true,
    "ecommerce_store": true,
    "jazzcash_integration": true,
    "easypaisa_integration": true,
    "inventory_management": true,
    "admin_panel": true,
    "social_media_integration": true,
    "whatsapp_business": true,
    "google_my_business": true,
    "revisions": 3,
    "support_days": 30
  }
}
```

**Expected Response (200):**
```json
{
  "package_type": "standard",
  "title": "Professional Business Website + E-commerce",
  "description": "Complete solution for Pakistani businesses wanting online sales",
  "price": 35000,
  "delivery_time": 10,
  "revision_count": 3,
  "features": {
    "pages": 10,
    "responsive_design": true,
    "advanced_seo": true,
    "contact_forms": true,
    "urdu_english_bilingual": true,
    "ecommerce_store": true,
    "jazzcash_integration": true,
    "easypaisa_integration": true,
    "inventory_management": true,
    "admin_panel": true,
    "social_media_integration": true,
    "whatsapp_business": true,
    "google_my_business": true,
    "revisions": 3,
    "support_days": 30
  },
  "package_id": 5,
  "gig_id": 2,
  "is_active": true,
  "created_at": "2025-05-27T11:45:26.103000",
  "updated_at": "2025-05-27T11:45:26.103000"
}
```

### Step 8: Switch to Buyer (Ahmed)

#### Login as Ahmed

**Endpoint:** `POST /api/auth/token`

**Request (Form Data):**
```
username: ahmed.buyer@gmail.com
password: ahmed123456
```

**Expected Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2IiwiZXhwIjoxNzQ4MzQ4MTIxfQ.rnMNdujmfehgFUwrs-pH6h4Sgn9k30qjHFFB9xxccs8",
  "token_type": "bearer"
}
```

**Update Authorization:** Use Ahmed's new token in the Authorize section.

### Step 9: Browse Gigs

**Endpoint:** `GET /api/gigs/`

**Parameters:**
- skip: 0
- limit: 20

**Expected Response (200):**
```json
[
  {
    "title": "I will develop a professional WordPress website for Pakistani businesses",
    "description": "🇵🇰 Pakistani Developer - Expert WordPress Solutions...",
    "category_id": 5,
    "subcategory_id": 9,
    "gig_metadata": {
      "target_market": "Pakistan",
      "languages_supported": ["Urdu", "English"],
      "business_types": ["Small Business", "E-commerce", "Services", "Restaurants"],
      "payment_gateways": ["JazzCash", "EasyPaisa", "Bank Transfer"],
      "tech_stack": ["WordPress", "Elementor", "WooCommerce", "PHP", "MySQL"]
    },
    "search_tags": "wordpress, pakistan, urdu, website, business, ecommerce, jazzcash, easypaisa, islamabad, karachi, lahore",
    "gig_id": 2,
    "seller_id": 2,
    "is_featured": false,
    "is_active": true,
    "impression_count": 1,
    "click_count": 0,
    "conversion_rate": null,
    "total_orders": 0,
    "total_reviews": 0,
    "ranking_score": 0.0,
    "created_at": "2025-05-27T11:45:24.983000",
    "updated_at": "2025-05-27T11:45:28.180000"
  }
]
```

### Step 10: Create Order

**Endpoint:** `POST /api/orders/`

**Request Body:**
```json
{
  "gig_id": 2,
  "package_id": 5,
  "requirements": "Assalam o Alaikum Sajjad bhai!\n\nI need a website for my family's restaurant in Islamabad. Here are the details:\n\n🏪 Business: Ahmed's Family Restaurant\n📍 Location: F-7 Markaz, Islamabad\n🍽️ Type: Pakistani & Chinese food\n\n📋 Requirements:\n1. Menu display with prices in PKR\n2. Online ordering system\n3. JazzCash payment integration\n4. WhatsApp ordering option\n5. Urdu/English language support\n6. Google Maps integration\n7. Photo gallery of our dishes\n8. Customer reviews section\n9. Contact forms\n10. Social media links (Facebook, Instagram)\n\n🎨 Design:\n- Colors: Green, white (Pakistan flag colors)\n- Modern but family-friendly design\n- Mobile-friendly for Pakistani customers\n\n📱 Special Features:\n- WhatsApp click-to-order button\n- JazzCash/EasyPaisa payment options\n- Delivery areas in Islamabad\n- Ramadan special menu section\n\n📞 Contact: +92-300-1234567\n\nPlease let me know if you need any additional information. JazakAllah!"
}
```

**Expected Response (200):**
```json
{
  "gig_id": 2,
  "package_id": 5,
  "requirements": "Assalam o Alaikum Sajjad bhai!\n\nI need a website for my family's restaurant in Islamabad...",
  "order_id": 2,
  "buyer_id": 6,
  "seller_id": 5,
  "custom_offer_id": null,
  "price": 35000,
  "delivery_time": 10,
  "expected_delivery_date": "2025-06-06T11:45:29.250000",
  "actual_delivery_date": null,
  "revision_count": 3,
  "revisions_used": 0,
  "status": "pending",
  "is_late": false,
  "created_at": "2025-05-27T11:45:29.253000",
  "updated_at": "2025-05-27T11:45:29.253000"
}
```

### Step 11: Send Message

**Endpoint:** `POST /api/messages/send`

**Request Body:**
```json
{
  "recipient_id": 5,
  "content": "Assalam o Alaikum Sajjad bhai! I just placed an order for our restaurant website. I'm really excited to work with a fellow Pakistani developer who understands our local market. \n\nI have a few additional questions:\n1. Can you add a special Ramadan menu section?\n2. Is it possible to integrate with our existing Facebook page?\n3. Can we have customer reviews in both Urdu and English?\n4. What about adding a prayer times widget?\n\nLooking forward to hearing from you!\n\nJazakAllah,\nAhmed Hassan\nAhmed's Family Restaurant\n+92-300-1234567",
  "attachment_url": null
}
```

**Expected Response (200):**
```json
{
  "content": "Assalam o Alaikum Sajjad bhai! I just placed an order for our restaurant website...",
  "attachment_url": null,
  "message_id": 2,
  "conversation_id": "1-6",
  "sender_id": 6,
  "recipient_id": 5,
  "is_read": false,
  "created_at": "2025-05-27T11:45:30.337000"
}
```

### Step 12: Switch Back to Seller (Sajjad)

1. Login again as Sajjad to get a fresh token
2. Update authorization
3. View seller orders: `GET /api/orders/seller`

### Step 13: Deliver Order

**Endpoint:** `POST /api/orders/2/deliver`

**Request Body:**
```json
{
  "message": "Assalam o Alaikum Ahmed bhai!\n\nAlhamdulillah! Your restaurant website is ready! 🎉\n\n🌟 What I've delivered:\n✅ Beautiful Pakistani-themed design with green/white colors\n✅ Complete menu with prices in PKR\n✅ JazzCash & EasyPaisa payment integration\n✅ WhatsApp ordering system\n✅ Bilingual support (Urdu/English)\n✅ Google Maps integration for F-7 location\n✅ Photo gallery for your delicious dishes\n✅ Customer review system (Urdu/English)\n✅ Contact forms with Pakistani phone format\n✅ Social media integration (Facebook/Instagram)\n✅ Mobile-responsive design\n✅ Prayer times widget for Islamabad\n✅ Special Ramadan menu section\n✅ Family package deals page\n\n🎯 Bonus features added:\n✅ Eid special menu section\n✅ Catering services page\n✅ Customer testimonials in both languages\n✅ Iftar/Sehri timings display\n✅ Pakistani cultural elements\n\n🔗 Website URL: https://ahmed-family-restaurant.pk\n📱 Test on mobile: Fully responsive\n💳 Payment testing: JazzCash sandbox working\n\nPlease review everything and let me know if you need any adjustments. I'm confident your customers will love the cultural touch and modern functionality!\n\nMay Allah bless your business!\n\nJazakAllah,\nSajjad",
  "files": {
    "website_url": "https://ahmed-family-restaurant.pk",
    "admin_panel": "https://ahmed-family-restaurant.pk/wp-admin",
    "source_files": "https://drive.google.com/folder/ahmed-restaurant-files",
    "documentation": "https://docs.google.com/document/d/ahmed-website-guide",
    "training_video": "https://youtube.com/watch?v=ahmed-training-urdu",
    "backup_file": "https://drive.google.com/file/ahmed-website-backup.zip"
  },
  "is_final_delivery": true
}
```

**Expected Response (200):**
```json
{
  "message": "Order delivered successfully"
}
```

### Step 14: Complete Workflow (as Ahmed)

1. **Switch back to Ahmed** (login + update auth)
2. **Request revision:** `POST /api/orders/2/request-revision`
3. **Switch to Sajjad** and **deliver revision:** `POST /api/orders/2/deliver`
4. **Switch to Ahmed** and **complete order:** `POST /api/orders/2/complete`
5. **Create review:** `POST /api/reviews/`

---