USE [SlateDB2];
GO

-- Drop existing functions if they exist
IF OBJECT_ID('fn_GenerateConversationId', 'FN') IS NOT NULL DROP FUNCTION fn_GenerateConversationId;
IF OBJECT_ID('fn_CalculateRankingScore', 'FN') IS NOT NULL DROP FUNCTION fn_CalculateRankingScore;
IF OBJECT_ID('fn_GetSellerLevel', 'FN') IS NOT NULL DROP FUNCTION fn_GetSellerLevel;
IF OBJECT_ID('fn_EstimateDeliveryDate', 'FN') IS NOT NULL DROP FUNCTION fn_EstimateDeliveryDate;
IF OBJECT_ID('fn_GetEarningsByPeriod', 'TF') IS NOT NULL DROP FUNCTION fn_GetEarningsByPeriod;
GO

-- =====================================================
-- UTILITY FUNCTIONS
-- =====================================================

-- Generate conversation ID function
CREATE FUNCTION fn_GenerateConversationId(
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
GO

-- =====================================================
-- BUSINESS LOGIC FUNCTIONS
-- =====================================================

-- Calculate ranking score function
CREATE FUNCTION fn_CalculateRankingScore(
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
GO

-- Get seller level function
CREATE FUNCTION fn_GetSellerLevel(
    @seller_id INT
)
RETURNS NVARCHAR(20)
AS
BEGIN
    DECLARE @level NVARCHAR(20);
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
GO

-- =====================================================
-- DATE AND TIME FUNCTIONS
-- =====================================================

-- Estimate delivery date function
CREATE FUNCTION fn_EstimateDeliveryDate(
    @gig_id INT,
    @package_id INT,
    @order_date DATETIME2 = NULL
)
RETURNS DATETIME2
AS
BEGIN
    DECLARE @delivery_date DATETIME2;
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
GO

-- =====================================================
-- TABLE-VALUED FUNCTIONS
-- =====================================================

-- Get earnings by period function
CREATE FUNCTION fn_GetEarningsByPeriod(
    @seller_id INT,
    @start_date DATETIME2,
    @end_date DATETIME2
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
GO

PRINT 'All functions created successfully in SlateDB2!';
GO