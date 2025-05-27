USE [SlateDB2];
GO

-- Clear existing data (in dependency order)
DELETE FROM favorites;
DELETE FROM gig_tags;
DELETE FROM tags;
DELETE FROM seller_skills;
DELETE FROM skills;
DELETE FROM notifications;
DELETE FROM payments;
DELETE FROM reviews;
DELETE FROM order_revisions;
DELETE FROM order_deliveries;
DELETE FROM orders;
DELETE FROM offers;
DELETE FROM messages;
DELETE FROM gig_images;
DELETE FROM gig_packages;
DELETE FROM gigs;
DELETE FROM seller_profiles;
DELETE FROM categories;
DELETE FROM users;

-- Reset identity columns
DBCC CHECKIDENT ('users', RESEED, 0);
DBCC CHECKIDENT ('categories', RESEED, 0);
DBCC CHECKIDENT ('seller_profiles', RESEED, 0);
DBCC CHECKIDENT ('skills', RESEED, 0);
DBCC CHECKIDENT ('tags', RESEED, 0);
DBCC CHECKIDENT ('gigs', RESEED, 0);
DBCC CHECKIDENT ('gig_packages', RESEED, 0);
DBCC CHECKIDENT ('orders', RESEED, 0);
GO

-- =====================================================
-- TEST SCENARIO 1: BASIC USER AND SELLER SETUP
-- =====================================================

PRINT 'Creating Test Scenario 1: Basic User and Seller Setup';

-- Create main categories
INSERT INTO categories (name, description, icon, display_order, is_active) VALUES
('Graphics & Design', 'Logo design, web design, and more', 'design-icon', 1, 1),
('Digital Marketing', 'Social media, SEO, and more', 'marketing-icon', 2, 1),
('Writing & Translation', 'Content writing, translation services', 'writing-icon', 3, 1),
('Video & Animation', 'Video editing, animation services', 'video-icon', 4, 1),
('Programming & Tech', 'Web development, mobile apps, and more', 'programming-icon', 5, 1);

-- Create subcategories
INSERT INTO categories (parent_category_id, name, description, display_order, is_active) VALUES
(1, 'Logo Design', 'Professional logo design services', 1, 1),
(1, 'Web Design', 'Website design and UI/UX services', 2, 1),
(1, 'Illustration', 'Custom illustrations and drawings', 3, 1),
(5, 'Web Development', 'Frontend and backend development', 1, 1),
(5, 'Mobile Apps', 'iOS and Android app development', 2, 1),
(5, 'Databases', 'Database design and optimization', 3, 1);

-- Create test users
INSERT INTO users (email, password_hash, user_role, full_name, country, language, registration_date, is_active) VALUES
('john.buyer@test.com', '$2b$12$hash1', 'buyer', 'John Smith', 'United States', 'English', GETDATE(), 1),
('sarah.designer@test.com', '$2b$12$hash2', 'seller', 'Sarah Johnson', 'Canada', 'English', GETDATE(), 1),
('mike.developer@test.com', '$2b$12$hash3', 'seller', 'Mike Chen', 'United States', 'English', GETDATE(), 1),
('emma.writer@test.com', '$2b$12$hash4', 'seller', 'Emma Davis', 'United Kingdom', 'English', GETDATE(), 1),
('alex.both@test.com', '$2b$12$hash5', 'both', 'Alex Rodriguez', 'Spain', 'Spanish', GETDATE(), 1);

-- Create seller profiles
INSERT INTO seller_profiles (user_id, professional_title, description, languages, account_level, created_at, updated_at) VALUES
(2, 'Professional Graphic Designer', 'I create stunning logos and web designs with 5+ years of experience', '["English", "French"]', 'level_1', GETDATE(), GETDATE()),
(3, 'Full Stack Developer', 'Expert in React, Node.js, and database design. 200+ projects completed', '["English", "Mandarin"]', 'level_2', GETDATE(), GETDATE()),
(4, 'Content Writer & Translator', 'Professional copywriter and translator for English-Spanish content', '["English", "Spanish"]', 'new', GETDATE(), GETDATE()),
(5, 'Digital Marketing Expert', 'SEO specialist and social media manager with proven results', '["English", "Spanish", "Portuguese"]', 'level_1', GETDATE(), GETDATE());

-- Create skills
INSERT INTO skills (name, category_id, is_active) VALUES
('JavaScript', 5, 1),
('React', 5, 1),
('Node.js', 5, 1),
('Python', 5, 1),
('Photoshop', 1, 1),
('Illustrator', 1, 1),
('Figma', 1, 1),
('Logo Design', 1, 1),
('Web Design', 1, 1),
('Content Writing', 3, 1),
('SEO', 2, 1),
('Social Media Marketing', 2, 1);

-- Create seller skills relationships
INSERT INTO seller_skills (seller_id, skill_id, experience_level) VALUES
(1, 5, 'expert'),    -- Sarah: Photoshop
(1, 6, 'expert'),    -- Sarah: Illustrator
(1, 8, 'expert'),    -- Sarah: Logo Design
(1, 9, 'intermediate'), -- Sarah: Web Design
(2, 1, 'expert'),    -- Mike: JavaScript
(2, 2, 'expert'),    -- Mike: React
(2, 3, 'expert'),    -- Mike: Node.js
(2, 4, 'intermediate'), -- Mike: Python
(3, 10, 'expert'),   -- Emma: Content Writing
(4, 11, 'expert'),   -- Alex: SEO
(4, 12, 'expert');   -- Alex: Social Media Marketing

-- Create tags
INSERT INTO tags (name, frequency) VALUES
('website', 0), ('logo', 0), ('modern', 0), ('responsive', 0), ('ecommerce', 0),
('mobile-app', 0), ('react', 0), ('nodejs', 0), ('seo', 0), ('content', 0),
('social-media', 0), ('branding', 0), ('ui-design', 0), ('frontend', 0), ('backend', 0);

PRINT 'Test Scenario 1 completed: Users, sellers, categories, and skills created';

-- =====================================================
-- TEST SCENARIO 2: GIG CREATION WITH PACKAGES
-- =====================================================

PRINT 'Creating Test Scenario 2: Gig Creation with Packages';

-- Create gigs
INSERT INTO gigs (seller_id, category_id, subcategory_id, title, description, search_tags, requirements, is_featured, is_active, created_at, updated_at) VALUES
(1, 1, 6, 'Professional Logo Design', 'I will create a modern, professional logo for your business with unlimited revisions until you are 100% satisfied.', 'logo,design,branding,modern', 'Please provide: business name, preferred colors, industry type, any specific requirements', 1, 1, GETDATE(), GETDATE()),
(1, 1, 7, 'Modern Website Design', 'I will design a stunning, responsive website that converts visitors into customers.', 'website,design,responsive,modern', 'Website purpose, number of pages, color preferences, reference websites', 0, 1, GETDATE(), GETDATE()),
(2, 5, 9, 'React Web Application', 'I will develop a custom React web application with modern UI and clean code.', 'react,webapp,frontend,javascript', 'Project requirements, API details, design mockups or wireframes', 1, 1, GETDATE(), GETDATE()),
(2, 5, 10, 'Mobile App Development', 'I will create a cross-platform mobile app using React Native.', 'mobile,app,react-native,ios,android', 'App features, target platforms, design preferences', 0, 1, GETDATE(), GETDATE()),
(3, 3, NULL, 'SEO Article Writing', 'I will write engaging, SEO-optimized articles that rank on Google.', 'seo,content,writing,articles', 'Topic, target keywords, word count, target audience', 0, 1, GETDATE(), GETDATE());

-- Create gig packages (3 packages per gig)
INSERT INTO gig_packages (gig_id, package_type, title, description, price, delivery_time, revision_count, features, is_active, created_at, updated_at) VALUES
-- Logo Design Packages
(1, 'basic', 'Basic Logo', 'Simple logo design with 2 concepts', 5000, 3, 2, '["2 logo concepts", "PNG files", "Basic support"]', 1, GETDATE(), GETDATE()),
(1, 'standard', 'Professional Logo', 'Premium logo with branding package', 10000, 5, 3, '["5 logo concepts", "All file formats", "Brand guidelines", "Priority support"]', 1, GETDATE(), GETDATE()),
(1, 'premium', 'Complete Branding', 'Full branding package with extras', 20000, 7, 5, '["Unlimited concepts", "Full branding kit", "Business card design", "Social media kit", "24/7 support"]', 1, GETDATE(), GETDATE()),

-- Website Design Packages
(2, 'basic', 'Landing Page', 'Single page website design', 15000, 5, 2, '["1 page design", "Mobile responsive", "Basic optimization"]', 1, GETDATE(), GETDATE()),
(2, 'standard', 'Business Website', 'Multi-page business website', 35000, 10, 3, '["Up to 5 pages", "Contact forms", "SEO optimization", "Admin panel"]', 1, GETDATE(), GETDATE()),
(2, 'premium', 'E-commerce Site', 'Full e-commerce website', 75000, 15, 4, '["Unlimited pages", "Payment integration", "Inventory management", "Analytics setup", "1 month support"]', 1, GETDATE(), GETDATE()),

-- React App Packages
(3, 'basic', 'Simple App', 'Basic React application', 25000, 7, 2, '["Basic functionality", "Responsive design", "Source code"]', 1, GETDATE(), GETDATE()),
(3, 'standard', 'Advanced App', 'Full-featured React application', 50000, 14, 3, '["Advanced features", "API integration", "Testing", "Documentation"]', 1, GETDATE(), GETDATE()),
(3, 'premium', 'Enterprise App', 'Enterprise-grade application', 100000, 21, 4, '["Complex features", "Database design", "Performance optimization", "Deployment", "3 months support"]', 1, GETDATE(), GETDATE()),

-- Mobile App Packages
(4, 'basic', 'Simple Mobile App', 'Basic mobile app for one platform', 40000, 14, 2, '["Single platform", "Basic features", "App store submission"]', 1, GETDATE(), GETDATE()),
(4, 'standard', 'Cross-Platform App', 'App for iOS and Android', 75000, 21, 3, '["iOS & Android", "Advanced features", "Push notifications", "Analytics"]', 1, GETDATE(), GETDATE()),
(4, 'premium', 'Enterprise Mobile App', 'Full-featured enterprise app', 150000, 30, 4, '["All platforms", "Backend development", "Admin dashboard", "Maintenance", "App store optimization"]', 1, GETDATE(), GETDATE()),

-- SEO Article Packages
(5, 'basic', '500 Words Article', 'SEO-optimized article', 2000, 2, 1, '["500 words", "SEO optimization", "1 revision"]', 1, GETDATE(), GETDATE()),
(5, 'standard', '1000 Words Article', 'In-depth SEO article', 3500, 3, 2, '["1000 words", "Advanced SEO", "Meta descriptions", "2 revisions"]', 1, GETDATE(), GETDATE()),
(5, 'premium', '2000+ Words Guide', 'Comprehensive guide with extras', 7000, 5, 3, '["2000+ words", "Research included", "Images sourcing", "Social media posts", "3 revisions"]', 1, GETDATE(), GETDATE());

-- Create gig images
INSERT INTO gig_images (gig_id, image_url, is_thumbnail, display_order, created_at) VALUES
(1, '/images/gigs/logo-design-thumb.jpg', 1, 1, 1672531200.0),
(1, '/images/gigs/logo-design-1.jpg', 0, 2, 1672531200.0),
(1, '/images/gigs/logo-design-2.jpg', 0, 3, 1672531200.0),
(2, '/images/gigs/web-design-thumb.jpg', 1, 1, 1672531200.0),
(2, '/images/gigs/web-design-1.jpg', 0, 2, 1672531200.0),
(3, '/images/gigs/react-app-thumb.jpg', 1, 1, 1672531200.0),
(3, '/images/gigs/react-app-1.jpg', 0, 2, 1672531200.0),
(4, '/images/gigs/mobile-app-thumb.jpg', 1, 1, 1672531200.0),
(5, '/images/gigs/seo-writing-thumb.jpg', 1, 1, 1672531200.0);

-- Create gig tags relationships
INSERT INTO gig_tags (gig_id, tag_id) VALUES
(1, 2), (1, 3), (1, 12),  -- Logo: logo, modern, branding
(2, 1), (2, 4), (2, 13),  -- Website: website, responsive, ui-design
(3, 7), (3, 14), (3, 15), -- React: react, frontend, backend
(4, 6), (4, 7),           -- Mobile: mobile-app, react
(5, 9), (5, 10);          -- SEO: seo, content

PRINT 'Test Scenario 2 completed: Gigs, packages, images, and tags created';

-- =====================================================
-- TEST SCENARIO 3: ORDER LIFECYCLE
-- =====================================================

PRINT 'Creating Test Scenario 3: Order Lifecycle';

-- Create orders
INSERT INTO orders (gig_id, package_id, buyer_id, seller_id, requirements, price, delivery_time, expected_delivery_date, revision_count, revisions_used, status, is_late, created_at, updated_at) VALUES
(1, 1, 1, 2, 'Need a logo for my tech startup. Colors: blue and white. Modern, clean design.', 5000, 3, DATEADD(DAY, 3, GETDATE()), 2, 0, 'completed', 0, DATEADD(DAY, -10, GETDATE()), DATEADD(DAY, -3, GETDATE())),
(1, 2, 5, 2, 'Complete branding for restaurant. Need warm colors, elegant feel.', 10000, 5, DATEADD(DAY, 5, GETDATE()), 3, 1, 'delivered', 0, DATEADD(DAY, -7, GETDATE()), DATEADD(DAY, -1, GETDATE())),
(3, 4, 1, 3, 'E-commerce platform for selling electronics. Need user authentication, payment gateway.', 50000, 14, DATEADD(DAY, 14, GETDATE()), 3, 0, 'in_progress', 0, DATEADD(DAY, -5, GETDATE()), DATEADD(DAY, -5, GETDATE())),
(5, 7, 5, 4, 'SEO article about sustainable living. Target keyword: eco-friendly lifestyle', 2000, 2, DATEADD(DAY, 2, GETDATE()), 1, 0, 'pending', 0, GETDATE(), GETDATE());

-- Create payments
INSERT INTO payments (order_id, amount, platform_fee, seller_amount, currency, payment_method, status, created_at) VALUES
(1, 5000, 1000, 4000, 'USD', 'credit_card', 'completed', DATEADD(DAY, -10, GETDATE())),
(2, 10000, 2000, 8000, 'USD', 'credit_card', 'pending', DATEADD(DAY, -7, GETDATE())),
(3, 50000, 10000, 40000, 'USD', 'paypal', 'pending', DATEADD(DAY, -5, GETDATE())),
(4, 2000, 400, 1600, 'USD', 'credit_card', 'pending', GETDATE());

-- Create order deliveries
INSERT INTO order_deliveries (order_id, message, files, delivered_at, is_final_delivery) VALUES
(1, 'Here is your completed logo design. Files include PNG, SVG, and AI formats.', '["logo-final.png", "logo-vector.svg", "logo-source.ai"]', DATEADD(DAY, -7, GETDATE()), 1),
(2, 'Initial logo concepts for your review. Please let me know which direction you prefer.', '["concept-1.png", "concept-2.png", "concept-3.png"]', DATEADD(DAY, -3, GETDATE()), 0),
(2, 'Revised logo based on your feedback. This is the final version.', '["logo-final-revised.png", "branding-guide.pdf"]', DATEADD(DAY, -1, GETDATE()), 1),
(3, 'Initial wireframes and database schema for your review.', '["wireframes.pdf", "database-schema.sql"]', DATEADD(DAY, -2, GETDATE()), 0);

-- Create order revisions
INSERT INTO order_revisions (order_id, requested_by, request_message, request_date, status) VALUES
(2, 5, 'Could you make the logo more elegant and change the font to something more modern?', DATEADD(DAY, -4, GETDATE()), 'accepted');

-- Create reviews
INSERT INTO reviews (order_id, reviewer_id, reviewee_id, communication_rating, service_rating, recommendation_rating, overall_rating, comment, created_at) VALUES
(1, 1, 2, 5, 5, 5, 5.0, 'Amazing work! Sarah delivered exactly what I wanted. Great communication and fast delivery.', DATEADD(DAY, -3, GETDATE()));

-- Create messages
INSERT INTO messages (conversation_id, sender_id, recipient_id, content, is_read, created_at) VALUES
('1-2', 1, 2, 'Hi Sarah, I saw your logo design gig and I am interested. Can you do a logo for a tech startup?', 1, DATEADD(DAY, -12, GETDATE())),
('1-2', 2, 1, 'Hi John! Yes, I would love to help with your logo. What style are you looking for?', 1, DATEADD(DAY, -12, GETDATE())),
('1-2', 1, 2, 'I need something modern and clean. Blue and white colors. Can you send me some samples?', 1, DATEADD(DAY, -11, GETDATE())),
('1-3', 1, 3, 'Hi Mike, interested in your React development services. Need an e-commerce platform.', 1, DATEADD(DAY, -6, GETDATE())),
('1-3', 3, 1, 'Hello! I can definitely help with that. What features do you need?', 1, DATEADD(DAY, -6, GETDATE())),
('3-5', 3, 5, 'Hey Alex, do you provide SEO consultation along with article writing?', 0, DATEADD(DAY, -1, GETDATE()));

-- Create offers
INSERT INTO offers (seller_id, buyer_id, title, description, price, delivery_time, revision_count, expiry_date, status, created_at, updated_at) VALUES
(2, 1, 'Custom Mobile App UI Design', 'I will create a custom UI design for your mobile app with modern aesthetics', 15000, 7, 3, DATEADD(DAY, 7, GETDATE()), 'pending', DATEADD(DAY, -2, GETDATE()), DATEADD(DAY, -2, GETDATE())),
(3, 5, 'Database Optimization Service', 'I will optimize your database for better performance and scalability', 8000, 5, 1, DATEADD(DAY, 5, GETDATE()), 'pending', DATEADD(DAY, -1, GETDATE()), DATEADD(DAY, -1, GETDATE()));

-- Create notifications
INSERT INTO notifications (user_id, type, content, related_entity_id, related_entity_type, created_at) VALUES
(2, 'new_order', 'You have received a new order', 1, 'order', DATEADD(DAY, -10, GETDATE())),
(1, 'order_delivered', 'Your order has been delivered', 1, 'order', DATEADD(DAY, -7, GETDATE())),
(2, 'order_completed', 'Your order has been completed and payment released', 1, 'order', DATEADD(DAY, -3, GETDATE())),
(2, 'new_message', 'You have received a new message', 1, 'message', DATEADD(DAY, -12, GETDATE())),
(1, 'new_offer', 'You have received a custom offer', 1, 'offer', DATEADD(DAY, -2, GETDATE())),
(5, 'revision_requested', 'A revision has been requested for your order', 2, 'order', DATEADD(DAY, -4, GETDATE()));

-- Create favorites
INSERT INTO favorites (user_id, gig_id, created_at) VALUES
(1, 2, DATEADD(DAY, -8, GETDATE())),
(1, 3, DATEADD(DAY, -6, GETDATE())),
(5, 1, DATEADD(DAY, -5, GETDATE())),
(5, 4, DATEADD(DAY, -3, GETDATE()));

PRINT 'Test Scenario 3 completed: Orders, payments, deliveries, reviews, messages, and notifications created';

-- =====================================================
-- TEST SCENARIO 4: UPDATE CALCULATED FIELDS
-- =====================================================

PRINT 'Creating Test Scenario 4: Update calculated fields and metrics';

-- Update seller ratings and metrics (simulating trigger effects)
UPDATE seller_profiles 
SET rating_average = 5.0, 
    completion_rate = 100,
    total_earnings = 4000,
    response_time = 30
WHERE seller_id = 1;

UPDATE seller_profiles 
SET rating_average = 0, 
    completion_rate = 75,
    total_earnings = 0,
    response_time = 60
WHERE seller_id = 2;

UPDATE seller_profiles 
SET rating_average = 0, 
    completion_rate = 50,
    total_earnings = 0,
    response_time = 45
WHERE seller_id = 3;

UPDATE seller_profiles 
SET rating_average = 0, 
    completion_rate = 100,
    total_earnings = 0,
    response_time = 120
WHERE seller_id = 4;

-- Update gig metrics
UPDATE gigs 
SET impression_count = 150, 
    click_count = 25, 
    total_orders = 2, 
    total_reviews = 1,
    ranking_score = 85.5,
    conversion_rate = 16.7
WHERE gig_id = 1;

UPDATE gigs 
SET impression_count = 200, 
    click_count = 15, 
    total_orders = 1, 
    total_reviews = 0,
    ranking_score = 72.3,
    conversion_rate = 7.5
WHERE gig_id = 2;

UPDATE gigs 
SET impression_count = 300, 
    click_count = 45, 
    total_orders = 1, 
    total_reviews = 0,
    ranking_score = 90.2,
    conversion_rate = 15.0
WHERE gig_id = 3;

UPDATE gigs 
SET impression_count = 180, 
    click_count = 20, 
    total_orders = 0, 
    total_reviews = 0,
    ranking_score = 65.8,
    conversion_rate = 11.1
WHERE gig_id = 4;

UPDATE gigs 
SET impression_count = 120, 
    click_count = 12, 
    total_orders = 1, 
    total_reviews = 0,
    ranking_score = 58.4,
    conversion_rate = 10.0
WHERE gig_id = 5;

-- Update tag frequencies
UPDATE tags SET frequency = 2 WHERE name = 'logo';
UPDATE tags SET frequency = 2 WHERE name = 'website';
UPDATE tags SET frequency = 2 WHERE name = 'modern';
UPDATE tags SET frequency = 1 WHERE name = 'responsive';
UPDATE tags SET frequency = 2 WHERE name = 'react';
UPDATE tags SET frequency = 1 WHERE name = 'mobile-app';
UPDATE tags SET frequency = 1 WHERE name = 'seo';
UPDATE tags SET frequency = 1 WHERE name = 'content';
UPDATE tags SET frequency = 1 WHERE name = 'branding';
UPDATE tags SET frequency = 1 WHERE name = 'ui-design';
UPDATE tags SET frequency = 1 WHERE name = 'frontend';
UPDATE tags SET frequency = 1 WHERE name = 'backend';

PRINT 'Test Scenario 4 completed: Calculated fields and metrics updated';

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

PRINT '==============================================';
PRINT 'SAMPLE DATA VERIFICATION';
PRINT '==============================================';

-- Check data counts
SELECT 'Users' AS Entity, COUNT(*) AS Count FROM users
UNION ALL
SELECT 'Seller Profiles', COUNT(*) FROM seller_profiles
UNION ALL
SELECT 'Categories', COUNT(*) FROM categories
UNION ALL
SELECT 'Skills', COUNT(*) FROM skills
UNION ALL
SELECT 'Gigs', COUNT(*) FROM gigs
UNION ALL
SELECT 'Gig Packages', COUNT(*) FROM gig_packages
UNION ALL
SELECT 'Orders', COUNT(*) FROM orders
UNION ALL
SELECT 'Payments', COUNT(*) FROM payments
UNION ALL
SELECT 'Reviews', COUNT(*) FROM reviews
UNION ALL
SELECT 'Messages', COUNT(*) FROM messages
UNION ALL
SELECT 'Notifications', COUNT(*) FROM notifications
UNION ALL
SELECT 'Favorites', COUNT(*) FROM favorites;

-- Show sample gigs with seller info
SELECT TOP 3
    g.title,
    u.full_name AS seller_name,
    c.name AS category,
    g.ranking_score,
    MIN(gp.price) AS starting_price
FROM gigs g
JOIN seller_profiles sp ON g.seller_id = sp.seller_id
JOIN users u ON sp.user_id = u.user_id
JOIN categories c ON g.category_id = c.category_id
JOIN gig_packages gp ON g.gig_id = gp.gig_id
GROUP BY g.gig_id, g.title, u.full_name, c.name, g.ranking_score
ORDER BY g.ranking_score DESC;

-- Show orders with status
SELECT 
    o.order_id,
    g.title AS gig_title,
    bu.full_name AS buyer,
    su.full_name AS seller,
    o.status,
    o.price/100.0 AS price_dollars
FROM orders o
JOIN gigs g ON o.gig_id = g.gig_id
JOIN users bu ON o.buyer_id = bu.user_id
JOIN users su ON o.seller_id = su.user_id;

