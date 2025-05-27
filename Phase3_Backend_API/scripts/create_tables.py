import os
import sys
from sqlalchemy import text

# Add the parent directory to the Python path so we can import the app module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can import from app
from app.database.session import engine, Base
from app.models import *

def create_tables():
    """Create all tables defined in the models"""
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

def create_triggers():
    conn = engine.connect()
    
    # FIXED: Limit Gigs Per Seller - Added SET NOCOUNT ON and proper structure
    limit_gigs_per_seller = """
    CREATE OR ALTER TRIGGER trg_limit_gigs_per_seller
    ON gigs
    FOR INSERT, UPDATE
    AS
    BEGIN
        SET NOCOUNT ON;
        
        DECLARE @seller_id INT;
        DECLARE @gig_count INT;
        
        SELECT @seller_id = seller_id FROM inserted;
        
        SELECT @gig_count = COUNT(*) 
        FROM gigs 
        WHERE seller_id = @seller_id AND is_active = 1;
        
        IF @gig_count > 5
        BEGIN
            RAISERROR('A seller cannot have more than 5 active gigs.', 16, 1);
            ROLLBACK TRANSACTION;
        END
    END
    """
    
    # FIXED: Calculate Overall Rating
    calculate_overall_rating = """
    CREATE OR ALTER TRIGGER trg_calculate_overall_rating
    ON reviews
    FOR INSERT, UPDATE
    AS
    BEGIN
        SET NOCOUNT ON;
        
        UPDATE reviews
        SET overall_rating = (communication_rating + service_rating + recommendation_rating) / 3.0
        WHERE review_id IN (SELECT review_id FROM inserted);
    END
    """
    
    # FIXED: Update Seller Rating
    update_seller_rating = """
    CREATE OR ALTER TRIGGER trg_update_seller_rating
    ON reviews
    FOR INSERT, UPDATE, DELETE
    AS
    BEGIN
        SET NOCOUNT ON;
        
        -- Update for inserted/updated records
        IF EXISTS (SELECT 1 FROM inserted)
        BEGIN
            UPDATE sp
            SET rating_average = (
                SELECT AVG(CAST(r.overall_rating AS FLOAT))
                FROM reviews r
                JOIN orders o ON r.order_id = o.order_id
                WHERE o.seller_id = sp.user_id
            )
            FROM seller_profiles sp
            WHERE sp.user_id IN (
                SELECT DISTINCT o.seller_id 
                FROM orders o 
                JOIN inserted i ON o.order_id = i.order_id
            );
        END
        
        -- Update for deleted records
        IF EXISTS (SELECT 1 FROM deleted)
        BEGIN
            UPDATE sp
            SET rating_average = (
                SELECT AVG(CAST(r.overall_rating AS FLOAT))
                FROM reviews r
                JOIN orders o ON r.order_id = o.order_id
                WHERE o.seller_id = sp.user_id
            )
            FROM seller_profiles sp
            WHERE sp.user_id IN (
                SELECT DISTINCT o.seller_id 
                FROM orders o 
                JOIN deleted d ON o.order_id = d.order_id
            );
        END
    END
    """
    
    # FIXED: Update Gig Ranking - Only on UPDATE, not INSERT
    update_gig_ranking = """
    CREATE OR ALTER TRIGGER trg_update_gig_ranking
    ON orders
    FOR UPDATE
    AS
    BEGIN
        SET NOCOUNT ON;
        
        -- Only update when order status changes to completed
        IF UPDATE(status)
        BEGIN
            UPDATE g
            SET ranking_score = (
                COALESCE(g.total_orders, 0) * 0.4 +
                COALESCE(g.total_reviews, 0) * 0.3 +
                CASE WHEN g.is_featured = 1 THEN 10 ELSE 0 END +
                COALESCE(g.impression_count, 0) * 0.01
            )
            FROM gigs g
            INNER JOIN inserted i ON g.gig_id = i.gig_id
            WHERE i.status = 'completed';
        END
    END
    """
    
    # FIXED: Order Completion
    order_completion = """
    CREATE OR ALTER TRIGGER trg_order_completion
    ON orders
    FOR UPDATE
    AS
    BEGIN
        SET NOCOUNT ON;
        
        -- Check if status changed to completed
        IF EXISTS (
            SELECT 1 FROM inserted i
            JOIN deleted d ON i.order_id = d.order_id
            WHERE i.status = 'completed' AND d.status <> 'completed'
        )
        BEGIN
            -- Update gig metrics
            UPDATE g
            SET 
                total_orders = total_orders + 1
            FROM gigs g
            JOIN inserted i ON g.gig_id = i.gig_id
            WHERE i.status = 'completed';
        END
    END
    """
    
    # FIXED: Offer Expiration
    offer_expiration = """
    CREATE OR ALTER TRIGGER trg_offer_expiration
    ON offers
    FOR INSERT, UPDATE
    AS
    BEGIN
        SET NOCOUNT ON;
        
        UPDATE offers
        SET status = 'expired'
        WHERE status = 'pending' AND expiry_date < GETDATE()
        AND offer_id IN (SELECT offer_id FROM inserted);
    END
    """
    
    # Execute all trigger creation statements
    try:
        conn.execute(text(limit_gigs_per_seller))
        conn.execute(text(calculate_overall_rating))
        conn.execute(text(update_seller_rating))
        conn.execute(text(update_gig_ranking))
        conn.execute(text(order_completion))
        conn.execute(text(offer_expiration))
        conn.commit()
        print("Fixed triggers created successfully.")
    except Exception as e:
        print(f"Error creating triggers: {e}")
    finally:
        conn.close()

def create_stored_procedures():
    """Create SQL Server stored procedures"""
    conn = engine.connect()
    
    # CreateUser procedure
    create_user = """
    CREATE OR ALTER PROCEDURE sp_CreateUser
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
    """
    
    # CreateSellerProfile procedure
    create_seller_profile = """
    CREATE OR ALTER PROCEDURE sp_CreateSellerProfile
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
    """
    
    # CreateGig procedure
    create_gig = """
    CREATE OR ALTER PROCEDURE sp_CreateGig
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
    """
    
    # PlaceOrder procedure
    place_order = """
    CREATE OR ALTER PROCEDURE sp_PlaceOrder
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
        DECLARE @expected_delivery_date DATETIME = DATEADD(DAY, @delivery_time, GETDATE());
        
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
    """
    
    # DeliverOrder procedure
    deliver_order = """
    CREATE OR ALTER PROCEDURE sp_DeliverOrder
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
    """
    
    # RequestRevision procedure
    request_revision = """
    CREATE OR ALTER PROCEDURE sp_RequestRevision
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
    """
    
    # CompleteOrder procedure
    complete_order = """
    CREATE OR ALTER PROCEDURE sp_CompleteOrder
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
    """
    
    # SendMessage procedure
    send_message = """
    CREATE OR ALTER PROCEDURE sp_SendMessage
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
    """
    
    # CreateCustomOffer procedure
    create_custom_offer = """
    CREATE OR ALTER PROCEDURE sp_CreateCustomOffer
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
        DECLARE @expiry_date DATETIME = DATEADD(DAY, @expiry_days, GETDATE());
        
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
    """
    
    # Execute all stored procedure creation statements
    try:
        conn.execute(text(create_user))
        conn.execute(text(create_seller_profile))
        conn.execute(text(create_gig))
        conn.execute(text(place_order))
        conn.execute(text(deliver_order))
        conn.execute(text(request_revision))
        conn.execute(text(complete_order))
        conn.execute(text(send_message))
        conn.execute(text(create_custom_offer))
        conn.commit()
        print("Stored procedures created successfully.")
    except Exception as e:
        print(f"Error creating stored procedures: {e}")
    finally:
        conn.close()

def create_functions():
    """Create SQL Server functions"""
    conn = engine.connect()
    
    # Generate conversation ID function
    generate_conversation_id = """
    CREATE OR ALTER FUNCTION fn_GenerateConversationId(
        @user_id1 INT,
        @user_id2 INT
    )
    RETURNS NVARCHAR(100)
    AS
    BEGIN
        DECLARE @conversation_id NVARCHAR(100);
        
        -- Always put smaller ID first for consistency
        SET @conversation_id = CASE 
                                  WHEN @user_id1 < @user_id2 THEN CAST(@user_id1 AS NVARCHAR) + '-' + CAST(@user_id2 AS NVARCHAR)
                                  ELSE CAST(@user_id2 AS NVARCHAR) + '-' + CAST(@user_id1 AS NVARCHAR)
                               END;
        
        RETURN @conversation_id;
    END
    """
    
    # Calculate ranking score function
    calculate_ranking_score = """
    CREATE OR ALTER FUNCTION fn_CalculateRankingScore(
        @seller_id INT,
        @gig_id INT
    )
    RETURNS FLOAT
    AS
    BEGIN
        DECLARE @ranking_score FLOAT = 0;
        DECLARE @seller_score FLOAT = 0;
        DECLARE @gig_score FLOAT = 0;
        DECLARE @content_score FLOAT = 0;
        
        -- Seller performance (40%)
        SELECT @seller_score = 0.4 * (
            COALESCE(sp.rating_average, 3) * 0.5 +
            COALESCE(sp.completion_rate, 80) * 0.002 +
            (100 - COALESCE(sp.response_time, 60)) * 0.003
        )
        FROM seller_profiles sp 
        WHERE sp.seller_id = @seller_id;
        
        -- Gig performance (35%)
        SELECT @gig_score = 0.35 * (
            COALESCE((SELECT COUNT(*) FROM orders WHERE gig_id = @gig_id AND status = 'completed'), 0) * 0.01 +
            COALESCE(g.conversion_rate, 2) * 0.1 +
            COALESCE(g.total_reviews, 0) * 0.05 +
            CASE 
                WHEN COALESCE((SELECT COUNT(*) FROM orders WHERE gig_id = @gig_id AND created_at > DATEADD(MONTH, -1, GETDATE())), 0) > 10 THEN 5
                ELSE COALESCE((SELECT COUNT(*) FROM orders WHERE gig_id = @gig_id AND created_at > DATEADD(MONTH, -1, GETDATE())), 0) * 0.5
            END
        )
        FROM gigs g
        WHERE g.gig_id = @gig_id;
        
        -- Content quality (25%)
        SELECT @content_score = 0.25 * (
            CASE WHEN LEN(g.description) > 1000 THEN 10
                 WHEN LEN(g.description) > 500 THEN 8
                 WHEN LEN(g.description) > 200 THEN 5
                 ELSE 3
            END * 0.4 +
            CASE WHEN (SELECT COUNT(*) FROM gig_images WHERE gig_id = @gig_id) >= 5 THEN 10 
                 WHEN (SELECT COUNT(*) FROM gig_images WHERE gig_id = @gig_id) >= 3 THEN 7
                 ELSE (SELECT COUNT(*) FROM gig_images WHERE gig_id = @gig_id) * 2
            END * 0.3 +
            CASE WHEN (SELECT COUNT(*) FROM gig_tags gt WHERE gt.gig_id = @gig_id) >= 5 THEN 10
                 ELSE (SELECT COUNT(*) FROM gig_tags gt WHERE gt.gig_id = @gig_id) * 2
            END * 0.3
        )
        FROM gigs g
        WHERE g.gig_id = @gig_id;
        
        -- Calculate final score
        SET @ranking_score = @seller_score + @gig_score + @content_score;
        
        RETURN @ranking_score;
    END
    """
    
    # Get seller level function
    get_seller_level = """
    CREATE OR ALTER FUNCTION fn_GetSellerLevel(
        @seller_id INT
    )
    RETURNS VARCHAR(20)
    AS
    BEGIN
        DECLARE @level VARCHAR(20);
        DECLARE @completed_orders INT;
        DECLARE @rating_average FLOAT;
        DECLARE @days_active INT;
        
        -- Get seller metrics
        SELECT 
            @completed_orders = COUNT(o.order_id),
            @rating_average = COALESCE(sp.rating_average, 0)
        FROM seller_profiles sp
        LEFT JOIN orders o ON o.seller_id = sp.user_id AND o.status = 'completed'
        WHERE sp.seller_id = @seller_id
        GROUP BY sp.rating_average;
        
        -- Calculate days since joining
        SELECT @days_active = DATEDIFF(DAY, MIN(u.registration_date), GETDATE())
        FROM users u
        JOIN seller_profiles sp ON u.user_id = sp.user_id
        WHERE sp.seller_id = @seller_id;
        
        -- Determine level based on metrics
        SET @level = 
            CASE
                WHEN @completed_orders >= 100 AND @rating_average >= 4.7 AND @days_active >= 180 THEN 'top_rated'
                WHEN @completed_orders >= 50 AND @rating_average >= 4.5 AND @days_active >= 90 THEN 'level_2'
                WHEN @completed_orders >= 10 AND @rating_average >= 4.0 AND @days_active >= 30 THEN 'level_1'
                ELSE 'new'
            END;
        
        RETURN @level;
    END
    """
    
    # Estimate delivery date function
    estimate_delivery_date = """
    CREATE OR ALTER FUNCTION fn_EstimateDeliveryDate(
        @gig_id INT,
        @package_id INT,
        @order_date DATETIME = NULL
    )
    RETURNS DATETIME
    AS
    BEGIN
        DECLARE @delivery_date DATETIME;
        DECLARE @delivery_time INT;
        
        -- Use current date if order_date not provided
        IF @order_date IS NULL
            SET @order_date = GETDATE();
        
        -- Get delivery time from package
        SELECT @delivery_time = delivery_time
        FROM gig_packages
        WHERE gig_id = @gig_id AND package_id = @package_id;
        
        -- Calculate delivery date
        SET @delivery_date = DATEADD(DAY, @delivery_time, @order_date);
        
        RETURN @delivery_date;
    END
    """
    
    # Get earnings by period function
    get_earnings_by_period = """
    CREATE OR ALTER FUNCTION fn_GetEarningsByPeriod(
        @seller_id INT,
        @start_date DATETIME,
        @end_date DATETIME
    )
    RETURNS TABLE
    AS
    RETURN
    (
        SELECT 
            CAST(YEAR(p.created_at) AS VARCHAR) + '-' + 
            RIGHT('0' + CAST(MONTH(p.created_at) AS VARCHAR), 2) AS period,
            SUM(p.seller_amount) AS earnings,
            COUNT(p.payment_id) AS completed_orders
        FROM payments p
        JOIN orders o ON p.order_id = o.order_id
        JOIN seller_profiles sp ON o.seller_id = sp.user_id
        WHERE sp.seller_id = @seller_id
          AND p.status = 'completed'
          AND p.created_at BETWEEN @start_date AND @end_date
        GROUP BY CAST(YEAR(p.created_at) AS VARCHAR) + '-' + 
                RIGHT('0' + CAST(MONTH(p.created_at) AS VARCHAR), 2)
    )
    """
    
    # Execute all function creation statements
    try:
        conn.execute(text(generate_conversation_id))
        conn.execute(text(calculate_ranking_score))
        conn.execute(text(get_seller_level))
        conn.execute(text(estimate_delivery_date))
        conn.execute(text(get_earnings_by_period))
        conn.commit()
        print("Functions created successfully.")
    except Exception as e:
        print(f"Error creating functions: {e}")
    finally:
        conn.close()

def create_views():
    """Create SQL Server views"""
    conn = engine.connect()
    
    # Gig listings view
    gig_listings = """
    CREATE OR ALTER VIEW vw_GigListings AS
    SELECT 
        g.gig_id,
        g.title,
        g.description,
        g.is_featured,
        g.ranking_score,
        c.category_id,
        c.name AS category_name,
        sc.category_id AS subcategory_id,
        sc.name AS subcategory_name,
        sp.seller_id,
        u.full_name AS seller_name,
        sp.professional_title,
        sp.rating_average,
        sp.account_level,
        sp.response_time,
        MIN(gp.price) AS starting_price,
        MIN(gp.delivery_time) AS min_delivery_time,
        (SELECT COUNT(*) FROM reviews r JOIN orders o ON r.order_id = o.order_id WHERE o.gig_id = g.gig_id) AS review_count,
        (SELECT TOP 1 gi.image_url FROM gig_images gi WHERE gi.gig_id = g.gig_id AND gi.is_thumbnail = 1) AS thumbnail_url
    FROM gigs g
    JOIN categories c ON g.category_id = c.category_id
    LEFT JOIN categories sc ON g.subcategory_id = sc.category_id
    JOIN seller_profiles sp ON g.seller_id = sp.seller_id
    JOIN users u ON sp.user_id = u.user_id
    JOIN gig_packages gp ON g.gig_id = gp.gig_id
    WHERE g.is_active = 1
    GROUP BY 
        g.gig_id, g.title, g.description, g.is_featured, g.ranking_score,
        c.category_id, c.name, sc.category_id, sc.name,
        sp.seller_id, u.full_name, sp.professional_title, sp.rating_average,
        sp.account_level, sp.response_time
    """
    
    # Seller dashboard view
    seller_dashboard = """
    CREATE OR ALTER VIEW vw_SellerDashboard AS
    SELECT 
        sp.seller_id,
        u.user_id,
        u.full_name,
        sp.professional_title,
        sp.rating_average,
        sp.account_level,
        sp.response_time,
        sp.completion_rate,
        sp.total_earnings,
        (SELECT COUNT(*) FROM gigs g WHERE g.seller_id = sp.seller_id AND g.is_active = 1) AS active_gigs,
        (SELECT COUNT(*) FROM orders o WHERE o.seller_id = u.user_id AND o.status = 'pending') AS pending_orders,
        (SELECT COUNT(*) FROM orders o WHERE o.seller_id = u.user_id AND o.status = 'in_progress') AS active_orders,
        (SELECT COUNT(*) FROM orders o WHERE o.seller_id = u.user_id AND o.status = 'delivered') AS delivered_orders,
        (SELECT COUNT(*) FROM orders o WHERE o.seller_id = u.user_id AND o.status = 'completed') AS completed_orders,
        (SELECT COUNT(*) FROM orders o WHERE o.seller_id = u.user_id AND o.status = 'cancelled') AS cancelled_orders,
        (SELECT AVG(completion_rate) FROM seller_profiles) AS avg_completion_rate,
        (SELECT AVG(rating_average) FROM seller_profiles WHERE rating_average IS NOT NULL) AS avg_rating,
        (SELECT TOP 1 gig_id FROM gigs WHERE seller_id = sp.seller_id AND is_active = 1 ORDER BY click_count DESC) AS best_performing_gig_id
    FROM seller_profiles sp
    JOIN users u ON sp.user_id = u.user_id
    """
    
    # Buyer dashboard view
    buyer_dashboard = """
    CREATE OR ALTER VIEW vw_BuyerDashboard AS
    SELECT 
        u.user_id AS buyer_id,
        u.full_name,
        (SELECT COUNT(*) FROM orders o WHERE o.buyer_id = u.user_id AND o.status = 'pending') AS pending_orders,
        (SELECT COUNT(*) FROM orders o WHERE o.buyer_id = u.user_id AND o.status = 'in_progress') AS active_orders,
        (SELECT COUNT(*) FROM orders o WHERE o.buyer_id = u.user_id AND o.status = 'delivered') AS delivered_orders,
        (SELECT COUNT(*) FROM orders o WHERE o.buyer_id = u.user_id AND o.status = 'completed') AS completed_orders,
        (SELECT COUNT(*) FROM orders o WHERE o.buyer_id = u.user_id AND o.status = 'cancelled') AS cancelled_orders,
        (SELECT COUNT(*) FROM favorites f WHERE f.user_id = u.user_id) AS saved_gigs,
        (SELECT COUNT(*) FROM offers offer_table WHERE offer_table.buyer_id = u.user_id AND offer_table.status = 'pending') AS pending_offers
    FROM users u
    WHERE u.user_role IN ('buyer', 'both')
    """
    
    # Order details view
    order_details = """
    CREATE OR ALTER VIEW vw_OrderDetails AS
    SELECT 
        o.order_id,
        o.gig_id,
        g.title AS gig_title,
        o.package_id,
        gp.package_type,
        gp.title AS package_title,
        o.buyer_id,
        bu.full_name AS buyer_name,
        o.seller_id,
        su.full_name AS seller_name,
        o.custom_offer_id,
        o.requirements,
        o.price,
        o.delivery_time,
        o.expected_delivery_date,
        o.actual_delivery_date,
        o.revision_count,
        o.revisions_used,
        o.status,
        o.is_late,
        o.created_at AS order_date,
        p.payment_id,
        p.status AS payment_status,
        p.seller_amount,
        p.platform_fee,
        r.review_id,
        r.overall_rating,
        r.comment AS review_comment,
        (SELECT COUNT(*) FROM order_deliveries od WHERE od.order_id = o.order_id) AS delivery_count,
        (SELECT MAX(od.delivered_at) FROM order_deliveries od WHERE od.order_id = o.order_id) AS last_delivery_date
    FROM orders o
    JOIN gigs g ON o.gig_id = g.gig_id
    JOIN gig_packages gp ON o.package_id = gp.package_id
    JOIN users bu ON o.buyer_id = bu.user_id
    JOIN users su ON o.seller_id = su.user_id
    LEFT JOIN payments p ON o.order_id = p.order_id
    LEFT JOIN reviews r ON o.order_id = r.order_id
    """
    
    # Message threads view
    message_threads = """
    CREATE OR ALTER VIEW vw_MessageThreads AS
    SELECT 
        m.conversation_id,
        u1.user_id AS user1_id,
        u1.full_name AS user1_name,
        u2.user_id AS user2_id,
        u2.full_name AS user2_name,
        MAX(m.created_at) AS last_message_date,
        (SELECT TOP 1 content FROM messages 
         WHERE conversation_id = m.conversation_id 
         ORDER BY created_at DESC) AS last_message_content,
        (SELECT COUNT(*) FROM messages 
         WHERE conversation_id = m.conversation_id 
         AND is_read = 0 
         AND recipient_id = u1.user_id) AS unread_count_user1,
        (SELECT COUNT(*) FROM messages 
         WHERE conversation_id = m.conversation_id 
         AND is_read = 0 
         AND recipient_id = u2.user_id) AS unread_count_user2
    FROM messages m
    JOIN users u1 ON CAST(SUBSTRING(m.conversation_id, 1, CHARINDEX('-', m.conversation_id) - 1) AS INT) = u1.user_id
    JOIN users u2 ON CAST(SUBSTRING(m.conversation_id, CHARINDEX('-', m.conversation_id) + 1, LEN(m.conversation_id)) AS INT) = u2.user_id
    GROUP BY 
        m.conversation_id, 
        u1.user_id, u1.full_name,
        u2.user_id, u2.full_name
    """
    
    # Top sellers view
    top_sellers = """
    CREATE OR ALTER VIEW vw_TopSellers AS
    SELECT 
        c.category_id,
        c.name AS category_name,
        sp.seller_id,
        u.user_id,
        u.full_name,
        sp.professional_title,
        sp.rating_average,
        sp.completion_rate,
        COALESCE((SELECT COUNT(*) FROM orders o 
                  JOIN gigs g ON o.gig_id = g.gig_id 
                  WHERE g.seller_id = sp.seller_id 
                  AND g.category_id = c.category_id 
                  AND o.status = 'completed'), 0) AS completed_orders_in_category,
        COALESCE((SELECT AVG(r.overall_rating) 
                  FROM reviews r 
                  JOIN orders o ON r.order_id = o.order_id 
                  JOIN gigs g ON o.gig_id = g.gig_id 
                  WHERE g.seller_id = sp.seller_id 
                  AND g.category_id = c.category_id), 0) AS category_rating
    FROM categories c
    CROSS JOIN seller_profiles sp
    JOIN users u ON sp.user_id = u.user_id
    WHERE EXISTS (SELECT 1 FROM gigs g 
                 WHERE g.seller_id = sp.seller_id 
                 AND g.category_id = c.category_id 
                 AND g.is_active = 1)
    """
    
    # Popular tags view
    popular_tags = """
    CREATE OR ALTER VIEW vw_PopularTags AS
    SELECT 
        t.tag_id,
        t.name AS tag_name,
        t.frequency,
        c.category_id,
        c.name AS category_name,
        (SELECT COUNT(DISTINCT g.gig_id) 
         FROM gigs g 
         JOIN gig_tags gt ON g.gig_id = gt.gig_id 
         WHERE gt.tag_id = t.tag_id 
         AND g.category_id = c.category_id) AS category_usage
    FROM tags t
    CROSS JOIN categories c
    WHERE t.frequency > 0
    AND EXISTS (SELECT 1 
                FROM gigs g 
                JOIN gig_tags gt ON g.gig_id = gt.gig_id 
                WHERE gt.tag_id = t.tag_id 
                AND g.category_id = c.category_id)
    """
    
    # Seller analytics view
    seller_analytics = """
    CREATE OR ALTER VIEW vw_SellerAnalytics AS
    SELECT 
        sp.seller_id,
        u.user_id,
        u.full_name,
        COALESCE((SELECT COUNT(*) FROM gigs g WHERE g.seller_id = sp.seller_id), 0) AS total_gigs,
        COALESCE((SELECT SUM(g.impression_count) FROM gigs g WHERE g.seller_id = sp.seller_id), 0) AS total_impressions,
        COALESCE((SELECT SUM(g.click_count) FROM gigs g WHERE g.seller_id = sp.seller_id), 0) AS total_clicks,
        CASE 
            WHEN (SELECT SUM(g.impression_count) FROM gigs g WHERE g.seller_id = sp.seller_id) > 0 
            THEN (SELECT SUM(g.click_count) FROM gigs g WHERE g.seller_id = sp.seller_id) * 100.0 / 
                 (SELECT SUM(g.impression_count) FROM gigs g WHERE g.seller_id = sp.seller_id)
            ELSE 0 
        END AS click_through_rate,
        COALESCE((SELECT COUNT(*) FROM orders o JOIN gigs g ON o.gig_id = g.gig_id WHERE g.seller_id = sp.seller_id), 0) AS total_orders,
        CASE 
            WHEN (SELECT SUM(g.click_count) FROM gigs g WHERE g.seller_id = sp.seller_id) > 0 
            THEN (SELECT COUNT(*) FROM orders o JOIN gigs g ON o.gig_id = g.gig_id WHERE g.seller_id = sp.seller_id) * 100.0 / 
                 (SELECT SUM(g.click_count) FROM gigs g WHERE g.seller_id = sp.seller_id)
            ELSE 0 
        END AS conversion_rate,
        COALESCE(sp.total_earnings, 0) AS total_earnings,
        COALESCE(sp.rating_average, 0) AS average_rating,
        COALESCE((SELECT COUNT(*) FROM reviews r 
                  JOIN orders o ON r.order_id = o.order_id 
                  JOIN gigs g ON o.gig_id = g.gig_id 
                  WHERE g.seller_id = sp.seller_id), 0) AS total_reviews,
        COALESCE(sp.response_time, 0) AS avg_response_time,
        COALESCE(sp.completion_rate, 0) AS completion_rate
    FROM seller_profiles sp
    JOIN users u ON sp.user_id = u.user_id
    """
    
    # Execute all view creation statements
    try:
        conn.execute(text(gig_listings))
        conn.execute(text(seller_dashboard))
        conn.execute(text(buyer_dashboard))
        conn.execute(text(order_details))
        conn.execute(text(message_threads))
        conn.execute(text(top_sellers))
        conn.execute(text(popular_tags))
        conn.execute(text(seller_analytics))
        conn.commit()
        print("Views created successfully.")
    except Exception as e:
        print(f"Error creating views: {e}")
    finally:
        conn.close()

def create_indexes():
    """Create SQL Server indexes for performance optimization"""
    conn = engine.connect()
    
    # Create indexes for performance optimization
    indexes = [
        "CREATE INDEX IX_Gigs_RankingScore ON gigs (ranking_score DESC)",
        "CREATE INDEX IX_Gigs_CategoryId ON gigs (category_id)",
        "CREATE INDEX IX_Orders_BuyerId ON orders (buyer_id)",
        "CREATE INDEX IX_Orders_SellerId ON orders (seller_id)",
        "CREATE INDEX IX_Messages_ConversationId ON messages (conversation_id)",
        "CREATE INDEX IX_GigTags_TagId ON gig_tags (tag_id)",
        "CREATE INDEX IX_Notifications_UserId_IsRead ON notifications (user_id, is_read)"
    ]
    
    try:
        for index in indexes:
            conn.execute(text(index))
        conn.commit()
        print("Indexes created successfully.")
    except Exception as e:
        print(f"Error creating indexes: {e}")
    finally:
        conn.close()

def seed_initial_data():
    """Seed the database with initial data"""
    conn = engine.connect()
    
    # Seed admin user
    admin_user = """
    INSERT INTO users (
        email, password_hash, user_role, full_name, 
        profile_picture, country, language, registration_date, is_active, last_login, updated_at, created_at
    )
    VALUES (
        'admin@slate.com', 
        '$2b$12$IJ5EKg2mQmQbxD5xHnVn0uZw.6GbTVNWEfVlX7mP26MNgvlFj6.6K', -- hashed 'admin123'
        'admin', 
        'System Administrator', 
        NULL, 
        'United States', 
        'English', 
        GETDATE(), 
        1, 
        GETDATE(),
        GETDATE(), -- updated_at value
        GETDATE()  -- created_at value
    )
    """
    
    # Seed initial categories
    categories = """
    -- Main categories
    INSERT INTO categories (name, description, icon, display_order, is_active)
    VALUES 
    ('Graphics & Design', 'Logo design, web design, and more', 'design-icon', 1, 1),
    ('Digital Marketing', 'Social media, SEO, and more', 'marketing-icon', 2, 1),
    ('Writing & Translation', 'Content writing, translation services', 'writing-icon', 3, 1),
    ('Video & Animation', 'Video editing, animation services', 'video-icon', 4, 1),
    ('Programming & Tech', 'Web development, mobile apps, and more', 'programming-icon', 5, 1);
    
    -- Subcategories for Graphics & Design
    INSERT INTO categories (parent_category_id, name, description, display_order, is_active)
    VALUES 
    (1, 'Logo Design', 'Professional logo design services', 1, 1),
    (1, 'Web Design', 'Website design and UI/UX services', 2, 1),
    (1, 'Illustration', 'Custom illustrations and drawings', 3, 1);
    
    -- Subcategories for Programming & Tech
    INSERT INTO categories (parent_category_id, name, description, display_order, is_active)
    VALUES 
    (5, 'Web Development', 'Frontend and backend development', 1, 1),
    (5, 'Mobile Apps', 'iOS and Android app development', 2, 1),
    (5, 'Databases', 'Database design and optimization', 3, 1);
    """
    
    # Seed initial skills
    skills = """
    -- Programming skills
    INSERT INTO skills (name, category_id, is_active)
    VALUES 
    ('JavaScript', 5, 1),
    ('Python', 5, 1),
    ('SQL', 5, 1),
    ('React', 5, 1),
    ('Node.js', 5, 1),
    ('PHP', 5, 1),
    ('Java', 5, 1),
    ('C#', 5, 1),
    ('Swift', 5, 1),
    ('Kotlin', 5, 1);
    
    -- Design skills
    INSERT INTO skills (name, category_id, is_active)
    VALUES 
    ('Photoshop', 1, 1),
    ('Illustrator', 1, 1),
    ('Figma', 1, 1),
    ('Sketch', 1, 1),
    ('UI/UX Design', 1, 1),
    ('Logo Design', 1, 1),
    ('Typography', 1, 1),
    ('3D Design', 1, 1);
    """
    
    # Seed initial tags
    tags = """
    -- Web development tags
    INSERT INTO tags (name, frequency)
    VALUES 
    ('website', 0),
    ('responsive', 0),
    ('frontend', 0),
    ('backend', 0),
    ('ecommerce', 0),
    ('wordpress', 0),
    ('shopify', 0),
    ('landing page', 0),
    ('web app', 0),
    ('mobile friendly', 0);
    
    -- Design tags
    INSERT INTO tags (name, frequency)
    VALUES 
    ('logo', 0),
    ('branding', 0),
    ('minimalist', 0),
    ('modern', 0),
    ('vintage', 0),
    ('illustration', 0),
    ('3d', 0),
    ('animation', 0),
    ('mockup', 0),
    ('ui design', 0);
    """
    
    try:
        conn.execute(text(admin_user))
        conn.execute(text(categories))
        conn.execute(text(skills))
        conn.execute(text(tags))
        conn.commit()
        print("Initial data seeded successfully.")
    except Exception as e:
        print(f"Error seeding initial data: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_tables()
    create_triggers()
    create_stored_procedures()
    create_functions()
    create_views()
    create_indexes()
    seed_initial_data()
    print("Database setup complete!")