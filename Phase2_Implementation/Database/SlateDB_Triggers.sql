USE [SlateDB2];
GO

-- Drop existing triggers if they exist
IF OBJECT_ID('trg_limit_gigs_per_seller', 'TR') IS NOT NULL DROP TRIGGER trg_limit_gigs_per_seller;
IF OBJECT_ID('trg_calculate_overall_rating', 'TR') IS NOT NULL DROP TRIGGER trg_calculate_overall_rating;
IF OBJECT_ID('trg_update_seller_rating', 'TR') IS NOT NULL DROP TRIGGER trg_update_seller_rating;
IF OBJECT_ID('trg_update_gig_ranking', 'TR') IS NOT NULL DROP TRIGGER trg_update_gig_ranking;
IF OBJECT_ID('trg_order_completion', 'TR') IS NOT NULL DROP TRIGGER trg_order_completion;
IF OBJECT_ID('trg_offer_expiration', 'TR') IS NOT NULL DROP TRIGGER trg_offer_expiration;
GO


-- Trigger: Limit Gigs Per Seller (Max 5 active gigs)
CREATE TRIGGER trg_limit_gigs_per_seller
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
GO

-- Trigger: Calculate Overall Rating in Reviews
CREATE TRIGGER trg_calculate_overall_rating
ON reviews
FOR INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE reviews
    SET overall_rating = (communication_rating + service_rating + recommendation_rating) / 3.0
    WHERE review_id IN (SELECT review_id FROM inserted);
END
GO

-- Trigger: Update Seller Rating Average
CREATE TRIGGER trg_update_seller_rating
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
GO

-- Trigger: Update Gig Ranking Score
CREATE TRIGGER trg_update_gig_ranking
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
GO

-- Trigger: Order Completion - Update Gig Metrics
CREATE TRIGGER trg_order_completion
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
GO

-- Trigger: Offer Expiration Check
CREATE TRIGGER trg_offer_expiration
ON offers
FOR INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if status is being set to 'pending' and expiry_date < current date
    -- Avoid infinite recursion by checking if we're not already updating to 'expired'
    IF NOT EXISTS (SELECT 1 FROM inserted WHERE status = 'expired')
    BEGIN
        UPDATE offers
        SET status = 'expired'
        WHERE status = 'pending' 
        AND expiry_date < GETDATE()
        AND offer_id IN (SELECT offer_id FROM inserted);
    END
END
GO
