IF NOT EXISTS (SELECT name FROM master.sys.databases WHERE name = N'SlateDB2')
BEGIN
    CREATE DATABASE [SlateDB2];
END
GO

USE [SlateDB2];
GO

-- Drop existing tables if they exist (in reverse dependency order)
IF OBJECT_ID('favorites', 'U') IS NOT NULL DROP TABLE favorites;
IF OBJECT_ID('gig_tags', 'U') IS NOT NULL DROP TABLE gig_tags;
IF OBJECT_ID('tags', 'U') IS NOT NULL DROP TABLE tags;
IF OBJECT_ID('seller_skills', 'U') IS NOT NULL DROP TABLE seller_skills;
IF OBJECT_ID('skills', 'U') IS NOT NULL DROP TABLE skills;
IF OBJECT_ID('notifications', 'U') IS NOT NULL DROP TABLE notifications;
IF OBJECT_ID('payments', 'U') IS NOT NULL DROP TABLE payments;
IF OBJECT_ID('reviews', 'U') IS NOT NULL DROP TABLE reviews;
IF OBJECT_ID('order_revisions', 'U') IS NOT NULL DROP TABLE order_revisions;
IF OBJECT_ID('order_deliveries', 'U') IS NOT NULL DROP TABLE order_deliveries;
IF OBJECT_ID('orders', 'U') IS NOT NULL DROP TABLE orders;
IF OBJECT_ID('offers', 'U') IS NOT NULL DROP TABLE offers;
IF OBJECT_ID('messages', 'U') IS NOT NULL DROP TABLE messages;
IF OBJECT_ID('gig_images', 'U') IS NOT NULL DROP TABLE gig_images;
IF OBJECT_ID('gig_packages', 'U') IS NOT NULL DROP TABLE gig_packages;
IF OBJECT_ID('gigs', 'U') IS NOT NULL DROP TABLE gigs;
IF OBJECT_ID('seller_profiles', 'U') IS NOT NULL DROP TABLE seller_profiles;
IF OBJECT_ID('categories', 'U') IS NOT NULL DROP TABLE categories;
IF OBJECT_ID('users', 'U') IS NOT NULL DROP TABLE users;

-- Users Table (Base entity for all system users)
CREATE TABLE users (
    user_id INT IDENTITY(1,1) PRIMARY KEY,
    email NVARCHAR(255) NOT NULL UNIQUE,
    password_hash NVARCHAR(255) NOT NULL,
    user_role NVARCHAR(20) NOT NULL CHECK (user_role IN ('buyer', 'seller', 'both', 'admin')),
    full_name NVARCHAR(255) NOT NULL,
    profile_picture NVARCHAR(1000) NULL,
    country NVARCHAR(100) NULL,
    language NVARCHAR(50) NULL,
    registration_date DATETIME2 NOT NULL DEFAULT GETDATE(),
    is_active BIT NOT NULL DEFAULT 1,
    last_login DATETIME2 NULL,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NOT NULL DEFAULT GETDATE()
);

-- Categories Table (Hierarchical service categories)
CREATE TABLE categories (
    category_id INT IDENTITY(1,1) PRIMARY KEY,
    parent_category_id INT NULL,
    name NVARCHAR(255) NOT NULL,
    description NVARCHAR(1000) NULL,
    icon NVARCHAR(255) NULL,
    display_order INT NULL,
    is_active BIT NOT NULL DEFAULT 1,
    FOREIGN KEY (parent_category_id) REFERENCES categories(category_id)
);

-- Seller Profiles Table (Extended seller information)
CREATE TABLE seller_profiles (
    seller_id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    professional_title NVARCHAR(255) NOT NULL,
    description NVARCHAR(4000) NULL,
    portfolio_links NVARCHAR(4000) NULL, -- JSON
    education NVARCHAR(1000) NULL,
    certifications NVARCHAR(1000) NULL,
    languages NVARCHAR(1000) NULL, -- JSON
    response_time INT NULL, -- Average in minutes
    completion_rate INT NULL, -- Percentage
    rating_average FLOAT NULL, -- Derived from reviews
    total_earnings INT NULL, -- In cents
    account_level NVARCHAR(20) NOT NULL DEFAULT 'new' CHECK (account_level IN ('new', 'level_1', 'level_2', 'top_rated')),
    personal_website NVARCHAR(255) NULL,
    social_media_links NVARCHAR(1000) NULL, -- JSON
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Skills Table (Seller skills catalog)
CREATE TABLE skills (
    skill_id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(255) NOT NULL UNIQUE,
    category_id INT NULL,
    is_active BIT NOT NULL DEFAULT 1,
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

-- Seller Skills Junction Table
CREATE TABLE seller_skills (
    seller_skill_id INT IDENTITY(1,1) PRIMARY KEY,
    seller_id INT NOT NULL,
    skill_id INT NOT NULL,
    experience_level NVARCHAR(20) NULL CHECK (experience_level IN ('beginner', 'intermediate', 'expert')),
    FOREIGN KEY (seller_id) REFERENCES seller_profiles(seller_id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id),
    UNIQUE (seller_id, skill_id)
);

-- =====================================================
-- SERVICE TABLES
-- =====================================================

-- Gigs Table (Services offered by sellers)
CREATE TABLE gigs (
    gig_id INT IDENTITY(1,1) PRIMARY KEY,
    seller_id INT NOT NULL,
    category_id INT NOT NULL,
    subcategory_id INT NULL,
    title NVARCHAR(255) NOT NULL,
    description NVARCHAR(4000) NOT NULL,
    gig_metadata NVARCHAR(4000) NULL, -- JSON
    search_tags NVARCHAR(500) NULL,
    requirements NVARCHAR(2000) NULL,
    faqs NVARCHAR(4000) NULL, -- JSON
    is_featured BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,
    impression_count INT NOT NULL DEFAULT 0,
    click_count INT NOT NULL DEFAULT 0,
    conversion_rate FLOAT NULL, -- Derived
    avg_response_time INT NULL, -- Minutes
    total_orders INT NOT NULL DEFAULT 0,
    total_reviews INT NOT NULL DEFAULT 0,
    ranking_score FLOAT NOT NULL DEFAULT 0, -- Calculated
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    FOREIGN KEY (seller_id) REFERENCES seller_profiles(seller_id),
    FOREIGN KEY (category_id) REFERENCES categories(category_id),
    FOREIGN KEY (subcategory_id) REFERENCES categories(category_id)
);

-- Gig Packages Table (Three-tier pricing structure)
CREATE TABLE gig_packages (
    package_id INT IDENTITY(1,1) PRIMARY KEY,
    gig_id INT NOT NULL,
    package_type NVARCHAR(20) NOT NULL CHECK (package_type IN ('basic', 'standard', 'premium')),
    title NVARCHAR(255) NOT NULL,
    description NVARCHAR(1000) NOT NULL,
    price INT NOT NULL CHECK (price > 0), -- In cents
    delivery_time INT NOT NULL CHECK (delivery_time > 0), -- In days
    revision_count INT NOT NULL DEFAULT 0 CHECK (revision_count >= 0),
    features NVARCHAR(2000) NULL, -- JSON
    is_active BIT NOT NULL DEFAULT 1,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    FOREIGN KEY (gig_id) REFERENCES gigs(gig_id) ON DELETE CASCADE,
    UNIQUE (gig_id, package_type)
);

-- Gig Images Table (Multiple images for each gig)
CREATE TABLE gig_images (
    image_id INT IDENTITY(1,1) PRIMARY KEY,
    gig_id INT NOT NULL,
    image_url NVARCHAR(1000) NOT NULL,
    is_thumbnail BIT NOT NULL DEFAULT 0,
    display_order INT NULL,
    created_at FLOAT NOT NULL, -- As per SQLAlchemy model
    FOREIGN KEY (gig_id) REFERENCES gigs(gig_id) ON DELETE CASCADE
);

-- Tags Table (Searchable tags for gigs)
CREATE TABLE tags (
    tag_id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(255) NOT NULL UNIQUE,
    frequency INT NOT NULL DEFAULT 0
);

-- Gig Tags Junction Table
CREATE TABLE gig_tags (
    gig_tag_id INT IDENTITY(1,1) PRIMARY KEY,
    gig_id INT NOT NULL,
    tag_id INT NOT NULL,
    FOREIGN KEY (gig_id) REFERENCES gigs(gig_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(tag_id),
    UNIQUE (gig_id, tag_id)
);

-- =====================================================
-- COMMUNICATION TABLES
-- =====================================================

-- Messages Table (Communication between users)
CREATE TABLE messages (
    message_id INT IDENTITY(1,1) PRIMARY KEY,
    conversation_id NVARCHAR(100) NOT NULL, -- Derived from user IDs
    sender_id INT NOT NULL,
    recipient_id INT NOT NULL,
    content NVARCHAR(4000) NOT NULL,
    attachment_url NVARCHAR(1000) NULL,
    is_read BIT NOT NULL DEFAULT 0,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    FOREIGN KEY (sender_id) REFERENCES users(user_id),
    FOREIGN KEY (recipient_id) REFERENCES users(user_id)
);

-- Offers Table (Custom offers from sellers to buyers)
CREATE TABLE offers (
    offer_id INT IDENTITY(1,1) PRIMARY KEY,
    seller_id INT NOT NULL,
    buyer_id INT NOT NULL,
    title NVARCHAR(255) NOT NULL,
    description NVARCHAR(2000) NOT NULL,
    price INT NOT NULL CHECK (price > 0), -- In cents
    delivery_time INT NOT NULL CHECK (delivery_time > 0), -- In days
    revision_count INT NOT NULL DEFAULT 0 CHECK (revision_count >= 0),
    expiry_date DATETIME2 NOT NULL,
    status NVARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected', 'expired')),
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    FOREIGN KEY (seller_id) REFERENCES seller_profiles(seller_id),
    FOREIGN KEY (buyer_id) REFERENCES users(user_id)
);

-- =====================================================
-- TRANSACTION TABLES
-- =====================================================

-- Orders Table (Transactions between buyers and sellers)
CREATE TABLE orders (
    order_id INT IDENTITY(1,1) PRIMARY KEY,
    gig_id INT NOT NULL,
    package_id INT NOT NULL,
    buyer_id INT NOT NULL,
    seller_id INT NOT NULL,
    custom_offer_id INT NULL,
    requirements NVARCHAR(2000) NULL,
    price INT NOT NULL CHECK (price > 0), -- In cents
    delivery_time INT NOT NULL CHECK (delivery_time > 0), -- In days
    expected_delivery_date DATETIME2 NOT NULL,
    actual_delivery_date DATETIME2 NULL,
    revision_count INT NOT NULL CHECK (revision_count >= 0), -- Total allowed
    revisions_used INT NOT NULL DEFAULT 0 CHECK (revisions_used >= 0),
    status NVARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'delivered', 'completed', 'cancelled', 'disputed')),
    is_late BIT NOT NULL DEFAULT 0,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    FOREIGN KEY (gig_id) REFERENCES gigs(gig_id),
    FOREIGN KEY (package_id) REFERENCES gig_packages(package_id),
    FOREIGN KEY (buyer_id) REFERENCES users(user_id),
    FOREIGN KEY (seller_id) REFERENCES users(user_id),
    FOREIGN KEY (custom_offer_id) REFERENCES offers(offer_id)
);

-- Order Deliveries Table (Deliverable files and messages for orders)
CREATE TABLE order_deliveries (
    delivery_id INT IDENTITY(1,1) PRIMARY KEY,
    order_id INT NOT NULL,
    message NVARCHAR(2000) NULL,
    files NVARCHAR(4000) NULL, -- JSON
    delivered_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    is_final_delivery BIT NOT NULL DEFAULT 0,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
);

-- Order Revisions Table (Revision requests and responses)
CREATE TABLE order_revisions (
    revision_id INT IDENTITY(1,1) PRIMARY KEY,
    order_id INT NOT NULL,
    requested_by INT NOT NULL,
    request_message NVARCHAR(2000) NOT NULL,
    request_date DATETIME2 NOT NULL DEFAULT GETDATE(),
    response_message NVARCHAR(2000) NULL,
    response_date DATETIME2 NULL,
    status NVARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected')),
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (requested_by) REFERENCES users(user_id)
);

-- Reviews Table (Feedback on completed orders)
CREATE TABLE reviews (
    review_id INT IDENTITY(1,1) PRIMARY KEY,
    order_id INT NOT NULL UNIQUE,
    reviewer_id INT NOT NULL,
    reviewee_id INT NOT NULL,
    communication_rating INT NOT NULL CHECK (communication_rating BETWEEN 1 AND 5),
    service_rating INT NOT NULL CHECK (service_rating BETWEEN 1 AND 5),
    recommendation_rating INT NOT NULL CHECK (recommendation_rating BETWEEN 1 AND 5),
    overall_rating FLOAT NOT NULL CHECK (overall_rating BETWEEN 1.0 AND 5.0), -- Calculated average
    comment NVARCHAR(2000) NULL,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    seller_response NVARCHAR(2000) NULL,
    seller_response_date DATETIME2 NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (reviewer_id) REFERENCES users(user_id),
    FOREIGN KEY (reviewee_id) REFERENCES users(user_id)
);

-- Payments Table (Payment records and transactions)
CREATE TABLE payments (
    payment_id INT IDENTITY(1,1) PRIMARY KEY,
    order_id INT NOT NULL,
    amount INT NOT NULL CHECK (amount > 0), -- In cents
    platform_fee INT NOT NULL CHECK (platform_fee >= 0), -- In cents
    seller_amount INT NOT NULL CHECK (seller_amount >= 0), -- In cents
    currency NVARCHAR(10) NOT NULL DEFAULT 'USD',
    payment_method NVARCHAR(50) NOT NULL,
    transaction_id NVARCHAR(255) NULL,
    status NVARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'refunded')),
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- Notifications Table (System notifications)
CREATE TABLE notifications (
    notification_id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,
    type NVARCHAR(50) NOT NULL,
    content NVARCHAR(1000) NOT NULL,
    is_read BIT NOT NULL DEFAULT 0,
    related_entity_id INT NULL,
    related_entity_type NVARCHAR(50) NULL,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Favorites Table (Saved gigs/sellers)
CREATE TABLE favorites (
    favorite_id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,
    gig_id INT NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (gig_id) REFERENCES gigs(gig_id) ON DELETE CASCADE,
    UNIQUE (user_id, gig_id)
);

