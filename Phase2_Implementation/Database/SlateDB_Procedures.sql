USE [SlateDB2];
GO

-- Drop existing procedures if they exist
IF OBJECT_ID('sp_CreateUser', 'P') IS NOT NULL DROP PROCEDURE sp_CreateUser;
IF OBJECT_ID('sp_CreateSellerProfile', 'P') IS NOT NULL DROP PROCEDURE sp_CreateSellerProfile;
IF OBJECT_ID('sp_CreateGig', 'P') IS NOT NULL DROP PROCEDURE sp_CreateGig;
IF OBJECT_ID('sp_PlaceOrder', 'P') IS NOT NULL DROP PROCEDURE sp_PlaceOrder;
IF OBJECT_ID('sp_DeliverOrder', 'P') IS NOT NULL DROP PROCEDURE sp_DeliverOrder;
IF OBJECT_ID('sp_RequestRevision', 'P') IS NOT NULL DROP PROCEDURE sp_RequestRevision;
IF OBJECT_ID('sp_CompleteOrder', 'P') IS NOT NULL DROP PROCEDURE sp_CompleteOrder;
IF OBJECT_ID('sp_SendMessage', 'P') IS NOT NULL DROP PROCEDURE sp_SendMessage;
IF OBJECT_ID('sp_CreateCustomOffer', 'P') IS NOT NULL DROP PROCEDURE sp_CreateCustomOffer;
GO


-- CreateUser procedure
CREATE PROCEDURE sp_CreateUser
    @email NVARCHAR(255),
    @password_hash NVARCHAR(255),
    @user_role NVARCHAR(20),
    @full_name NVARCHAR(255),
    @country NVARCHAR(100) = NULL,
    @language NVARCHAR(50) = NULL,
    @user_id INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Check if email already exists
    IF EXISTS (SELECT 1 FROM users WHERE email = @email)
    BEGIN
        RAISERROR('Email already exists', 16, 1);
        RETURN;
    END
    
    -- Insert new user
    INSERT INTO users (
        email, password_hash, user_role, full_name, 
        country, language, registration_date, is_active
    )
    VALUES (
        @email, @password_hash, @user_role, @full_name,
        @country, @language, GETDATE(), 1
    );
    
    SET @user_id = SCOPE_IDENTITY();
    RETURN;
END
GO

-- CreateSellerProfile procedure
CREATE PROCEDURE sp_CreateSellerProfile
    @user_id INT,
    @professional_title NVARCHAR(255),
    @description NVARCHAR(4000) = NULL,
    @languages NVARCHAR(1000) = NULL,
    @seller_id INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Check if user exists
    IF NOT EXISTS (SELECT 1 FROM users WHERE user_id = @user_id)
    BEGIN
        RAISERROR('User does not exist', 16, 1);
        RETURN;
    END
    
    -- Check if user already has a seller profile
    IF EXISTS (SELECT 1 FROM seller_profiles WHERE user_id = @user_id)
    BEGIN
        RAISERROR('User already has a seller profile', 16, 1);
        RETURN;
    END
    
    -- Insert seller profile
    INSERT INTO seller_profiles (
        user_id, professional_title, description,
        languages, account_level, created_at, updated_at
    )
    VALUES (
        @user_id, @professional_title, @description,
        @languages, 'new', GETDATE(), GETDATE()
    );
    
    SET @seller_id = SCOPE_IDENTITY();
    
    -- Update user role if needed
    UPDATE users
    SET user_role = CASE 
                       WHEN user_role = 'buyer' THEN 'both'
                       ELSE user_role
                     END
    WHERE user_id = @user_id AND user_role = 'buyer';
    
    RETURN;
END
GO

-- =====================================================
-- GIG MANAGEMENT PROCEDURES
-- =====================================================

-- CreateGig procedure
CREATE PROCEDURE sp_CreateGig
    @seller_id INT,
    @category_id INT,
    @subcategory_id INT = NULL,
    @title NVARCHAR(255),
    @description NVARCHAR(4000),
    @search_tags NVARCHAR(500) = NULL,
    @requirements NVARCHAR(2000) = NULL,
    @gig_id INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Check if seller exists
    IF NOT EXISTS (SELECT 1 FROM seller_profiles WHERE seller_id = @seller_id)
    BEGIN
        RAISERROR('Seller does not exist', 16, 1);
        RETURN;
    END
    
    -- Check if seller already has 5 active gigs
    IF (SELECT COUNT(*) FROM gigs WHERE seller_id = @seller_id AND is_active = 1) >= 5
    BEGIN
        RAISERROR('Seller already has maximum number of active gigs (5)', 16, 1);
        RETURN;
    END
    
    -- Check if category exists
    IF NOT EXISTS (SELECT 1 FROM categories WHERE category_id = @category_id)
    BEGIN
        RAISERROR('Category does not exist', 16, 1);
        RETURN;
    END
    
    -- Check if subcategory exists if provided
    IF @subcategory_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM categories 
        WHERE category_id = @subcategory_id AND parent_category_id = @category_id
    )
    BEGIN
        RAISERROR('Invalid subcategory', 16, 1);
        RETURN;
    END
    
    -- Insert gig
    INSERT INTO gigs (
        seller_id, category_id, subcategory_id, title, 
        description, search_tags, requirements, 
        is_featured, is_active, created_at, updated_at
    )
    VALUES (
        @seller_id, @category_id, @subcategory_id, @title,
        @description, @search_tags, @requirements,
        0, 1, GETDATE(), GETDATE()
    );
    
    SET @gig_id = SCOPE_IDENTITY();
    RETURN;
END
GO

-- =====================================================
-- ORDER MANAGEMENT PROCEDURES
-- =====================================================

-- PlaceOrder procedure
CREATE PROCEDURE sp_PlaceOrder
    @gig_id INT,
    @package_id INT,
    @buyer_id INT,
    @requirements NVARCHAR(2000) = NULL,
    @custom_offer_id INT = NULL,
    @order_id INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @seller_id INT;
    DECLARE @price INT;
    DECLARE @delivery_time INT;
    
    -- Get seller id from gig
    SELECT @seller_id = seller_id 
    FROM gigs 
    WHERE gig_id = @gig_id;
    
    -- Check if buyer exists
    IF NOT EXISTS (SELECT 1 FROM users WHERE user_id = @buyer_id)
    BEGIN
        RAISERROR('Buyer does not exist', 16, 1);
        RETURN;
    END
    
    -- Check if buyer is trying to order their own gig
    IF @buyer_id = (SELECT user_id FROM seller_profiles WHERE seller_id = @seller_id)
    BEGIN
        RAISERROR('Cannot order your own gig', 16, 1);
        RETURN;
    END
    
    -- Get package details
    SELECT @price = price, @delivery_time = delivery_time 
    FROM gig_packages 
    WHERE package_id = @package_id AND gig_id = @gig_id;
    
    -- Check if package exists for this gig
    IF @price IS NULL OR @delivery_time IS NULL
    BEGIN
        RAISERROR('Invalid package for this gig', 16, 1);
        RETURN;
    END
    
    -- Check custom offer if provided
    IF @custom_offer_id IS NOT NULL
    BEGIN
        -- Verify offer exists, is for this buyer, and is pending
        IF NOT EXISTS (
            SELECT 1 FROM offers 
            WHERE offer_id = @custom_offer_id 
              AND buyer_id = @buyer_id 
              AND seller_id = @seller_id
              AND status = 'pending'
        )
        BEGIN
            RAISERROR('Invalid custom offer', 16, 1);
            RETURN;
        END
        
        -- Use custom offer details
        SELECT @price = price, @delivery_time = delivery_time 
        FROM offers 
        WHERE offer_id = @custom_offer_id;
        
        -- Update offer status
        UPDATE offers
        SET status = 'accepted'
        WHERE offer_id = @custom_offer_id;
    END
    
    -- Calculate expected delivery date
    DECLARE @expected_delivery_date DATETIME2 = DATEADD(DAY, @delivery_time, GETDATE());
    
    -- Create order
    INSERT INTO orders (
        gig_id, package_id, buyer_id, seller_id,
        custom_offer_id, requirements, price,
        delivery_time, expected_delivery_date,
        revision_count, revisions_used,
        status, is_late, created_at, updated_at
    )
    VALUES (
        @gig_id, @package_id, @buyer_id, @seller_id,
        @custom_offer_id, @requirements, @price,
        @delivery_time, @expected_delivery_date,
        (SELECT revision_count FROM gig_packages WHERE package_id = @package_id), 0,
        'pending', 0, GETDATE(), GETDATE()
    );
    
    SET @order_id = SCOPE_IDENTITY();
    
    -- Create payment record
    DECLARE @platform_fee INT = ROUND(@price * 0.2, 0); -- 20% platform fee
    DECLARE @seller_amount INT = @price - @platform_fee;
    
    INSERT INTO payments (
        order_id, amount, platform_fee, seller_amount,
        currency, payment_method, status, created_at
    )
    VALUES (
        @order_id, @price, @platform_fee, @seller_amount,
        'USD', 'credit_card', 'pending', GETDATE()
    );
    
    -- Update gig metrics
    UPDATE gigs
    SET click_count = click_count + 1
    WHERE gig_id = @gig_id;
    
    -- Create notification for seller
    INSERT INTO notifications (
        user_id, type, content, related_entity_id,
        related_entity_type, created_at
    )
    VALUES (
        @seller_id, 'new_order', 
        'You have received a new order', 
        @order_id, 'order', GETDATE()
    );
    
    RETURN;
END
GO

-- DeliverOrder procedure
CREATE PROCEDURE sp_DeliverOrder
    @order_id INT,
    @seller_id INT,
    @message NVARCHAR(2000) = NULL,
    @files NVARCHAR(4000) = NULL,
    @is_final_delivery BIT = 1
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Check if order exists and belongs to seller
    IF NOT EXISTS (
        SELECT 1 FROM orders o
        JOIN seller_profiles sp ON o.seller_id = sp.user_id
        WHERE o.order_id = @order_id AND sp.seller_id = @seller_id
    )
    BEGIN
        RAISERROR('Order not found or does not belong to seller', 16, 1);
        RETURN;
    END
    
    -- Check if order is in a valid state for delivery
    IF NOT EXISTS (
        SELECT 1 FROM orders
        WHERE order_id = @order_id AND status IN ('pending', 'in_progress')
    )
    BEGIN
        RAISERROR('Order cannot be delivered in its current state', 16, 1);
        RETURN;
    END
    
    -- Create delivery record
    INSERT INTO order_deliveries (
        order_id, message, files, delivered_at, is_final_delivery
    )
    VALUES (
        @order_id, @message, @files, GETDATE(), @is_final_delivery
    );
    
    -- Update order status
    IF @is_final_delivery = 1
    BEGIN
        UPDATE orders
        SET 
            status = 'delivered',
            actual_delivery_date = GETDATE(),
            updated_at = GETDATE()
        WHERE order_id = @order_id;
        
        -- Create notification for buyer
        INSERT INTO notifications (
            user_id, type, content, related_entity_id,
            related_entity_type, created_at
        )
        VALUES (
            (SELECT buyer_id FROM orders WHERE order_id = @order_id),
            'order_delivered', 
            'Your order has been delivered', 
            @order_id, 'order', GETDATE()
        );
    END
    ELSE
    BEGIN
        -- Just update status to in_progress if not already
        UPDATE orders
        SET 
            status = 'in_progress',
            updated_at = GETDATE()
        WHERE order_id = @order_id AND status = 'pending';
    END
    
    RETURN;
END
GO

-- RequestRevision procedure
CREATE PROCEDURE sp_RequestRevision
    @order_id INT,
    @user_id INT,
    @request_message NVARCHAR(2000),
    @revision_id INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Check if order exists and user is buyer
    IF NOT EXISTS (
        SELECT 1 FROM orders
        WHERE order_id = @order_id AND buyer_id = @user_id
    )
    BEGIN
        RAISERROR('Order not found or user is not the buyer', 16, 1);
        RETURN;
    END
    
    -- Check if order is in a valid state for revision
    IF NOT EXISTS (
        SELECT 1 FROM orders
        WHERE order_id = @order_id AND status = 'delivered'
    )
    BEGIN
        RAISERROR('Order must be in delivered state to request revision', 16, 1);
        RETURN;
    END
    
    -- Check if buyer has revisions left
    DECLARE @revisions_allowed INT;
    DECLARE @revisions_used INT;
    
    SELECT 
        @revisions_allowed = revision_count,
        @revisions_used = revisions_used
    FROM orders
    WHERE order_id = @order_id;
    
    IF @revisions_used >= @revisions_allowed
    BEGIN
        RAISERROR('No revisions left for this order', 16, 1);
        RETURN;
    END
    
    -- Create revision request
    INSERT INTO order_revisions (
        order_id, requested_by, request_message,
        request_date, status
    )
    VALUES (
        @order_id, @user_id, @request_message,
        GETDATE(), 'pending'
    );
    
    SET @revision_id = SCOPE_IDENTITY();
    
    -- Update order
    UPDATE orders
    SET 
        status = 'in_progress',
        revisions_used = revisions_used + 1,
        updated_at = GETDATE()
    WHERE order_id = @order_id;
    
    -- Create notification for seller
    INSERT INTO notifications (
        user_id, type, content, related_entity_id,
        related_entity_type, created_at
    )
    VALUES (
        (SELECT seller_id FROM orders WHERE order_id = @order_id),
        'revision_requested', 
        'A revision has been requested for your order', 
        @order_id, 'order', GETDATE()
    );
    
    RETURN;
END
GO

-- CompleteOrder procedure
CREATE PROCEDURE sp_CompleteOrder
    @order_id INT,
    @user_id INT
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Check if order exists and user is buyer
    IF NOT EXISTS (
        SELECT 1 FROM orders
        WHERE order_id = @order_id AND buyer_id = @user_id
    )
    BEGIN
        RAISERROR('Order not found or user is not the buyer', 16, 1);
        RETURN;
    END
    
    -- Check if order is in a valid state for completion
    IF NOT EXISTS (
        SELECT 1 FROM orders
        WHERE order_id = @order_id AND status = 'delivered'
    )
    BEGIN
        RAISERROR('Order must be in delivered state to complete', 16, 1);
        RETURN;
    END
    
    -- Update order status
    UPDATE orders
    SET 
        status = 'completed',
        updated_at = GETDATE()
    WHERE order_id = @order_id;
    
    -- Update payment status
    UPDATE payments
    SET status = 'completed'
    WHERE order_id = @order_id;
    
    -- Create notification for seller
    INSERT INTO notifications (
        user_id, type, content, related_entity_id,
        related_entity_type, created_at
    )
    VALUES (
        (SELECT seller_id FROM orders WHERE order_id = @order_id),
        'order_completed', 
        'Your order has been completed and payment released', 
        @order_id, 'order', GETDATE()
    );
    
    RETURN;
END
GO

-- =====================================================
-- COMMUNICATION PROCEDURES
-- =====================================================

-- SendMessage procedure
CREATE PROCEDURE sp_SendMessage
    @sender_id INT,
    @recipient_id INT,
    @content NVARCHAR(4000),
    @attachment_url NVARCHAR(1000) = NULL,
    @message_id INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Check if sender exists
    IF NOT EXISTS (SELECT 1 FROM users WHERE user_id = @sender_id)
    BEGIN
        RAISERROR('Sender does not exist', 16, 1);
        RETURN;
    END
    
    -- Check if recipient exists
    IF NOT EXISTS (SELECT 1 FROM users WHERE user_id = @recipient_id)
    BEGIN
        RAISERROR('Recipient does not exist', 16, 1);
        RETURN;
    END
    
    -- Generate conversation ID (always smaller ID first)
    DECLARE @conversation_id NVARCHAR(100);
    SET @conversation_id = CASE 
                              WHEN @sender_id < @recipient_id THEN CAST(@sender_id AS NVARCHAR) + '-' + CAST(@recipient_id AS NVARCHAR)
                              ELSE CAST(@recipient_id AS NVARCHAR) + '-' + CAST(@sender_id AS NVARCHAR)
                           END;
    
    -- Insert message
    INSERT INTO messages (
        conversation_id, sender_id, recipient_id,
        content, attachment_url, is_read, created_at
    )
    VALUES (
        @conversation_id, @sender_id, @recipient_id,
        @content, @attachment_url, 0, GETDATE()
    );
    
    SET @message_id = SCOPE_IDENTITY();
    
    -- Create notification for recipient
    INSERT INTO notifications (
        user_id, type, content, related_entity_id,
        related_entity_type, created_at
    )
    VALUES (
        @recipient_id, 'new_message', 
        'You have received a new message', 
        @message_id, 'message', GETDATE()
    );
    
    RETURN;
END
GO

-- CreateCustomOffer procedure
CREATE PROCEDURE sp_CreateCustomOffer
    @seller_id INT,
    @buyer_id INT,
    @title NVARCHAR(255),
    @description NVARCHAR(2000),
    @price INT,
    @delivery_time INT,
    @revision_count INT = 0,
    @expiry_days INT = 7,
    @offer_id INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Check if seller exists
    IF NOT EXISTS (SELECT 1 FROM seller_profiles WHERE seller_id = @seller_id)
    BEGIN
        RAISERROR('Seller does not exist', 16, 1);
        RETURN;
    END
    
    -- Check if buyer exists
    IF NOT EXISTS (SELECT 1 FROM users WHERE user_id = @buyer_id)
    BEGIN
        RAISERROR('Buyer does not exist', 16, 1);
        RETURN;
    END
    
    -- Check if seller is trying to create an offer for themselves
    IF @buyer_id = (SELECT user_id FROM seller_profiles WHERE seller_id = @seller_id)
    BEGIN
        RAISERROR('Cannot create offer for yourself', 16, 1);
        RETURN;
    END
    
    -- Calculate expiry date
    DECLARE @expiry_date DATETIME2 = DATEADD(DAY, @expiry_days, GETDATE());
    
    -- Insert offer
    INSERT INTO offers (
        seller_id, buyer_id, title, description,
        price, delivery_time, revision_count,
        expiry_date, status, created_at, updated_at
    )
    VALUES (
        @seller_id, @buyer_id, @title, @description,
        @price, @delivery_time, @revision_count,
        @expiry_date, 'pending', GETDATE(), GETDATE()
    );
    
    SET @offer_id = SCOPE_IDENTITY();
    
    -- Create notification for buyer
    INSERT INTO notifications (
        user_id, type, content, related_entity_id,
        related_entity_type, created_at
    )
    VALUES (
        @buyer_id, 'new_offer', 
        'You have received a custom offer', 
        @offer_id, 'offer', GETDATE()
    );
    
    RETURN;
END
GO
