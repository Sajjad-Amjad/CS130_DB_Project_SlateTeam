USE [SlateDB2];
GO

-- Drop existing views if they exist
IF OBJECT_ID('vw_GigListings', 'V') IS NOT NULL DROP VIEW vw_GigListings;
IF OBJECT_ID('vw_SellerDashboard', 'V') IS NOT NULL DROP VIEW vw_SellerDashboard;
IF OBJECT_ID('vw_BuyerDashboard', 'V') IS NOT NULL DROP VIEW vw_BuyerDashboard;
IF OBJECT_ID('vw_OrderDetails', 'V') IS NOT NULL DROP VIEW vw_OrderDetails;
IF OBJECT_ID('vw_MessageThreads', 'V') IS NOT NULL DROP VIEW vw_MessageThreads;
IF OBJECT_ID('vw_TopSellers', 'V') IS NOT NULL DROP VIEW vw_TopSellers;
IF OBJECT_ID('vw_PopularTags', 'V') IS NOT NULL DROP VIEW vw_PopularTags;
IF OBJECT_ID('vw_SellerAnalytics', 'V') IS NOT NULL DROP VIEW vw_SellerAnalytics;
GO

-- Gig listings view
CREATE VIEW vw_GigListings AS
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
GO

-- =====================================================
-- DASHBOARD VIEWS
-- =====================================================

-- Seller dashboard view
CREATE VIEW vw_SellerDashboard AS
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
    (SELECT AVG(CAST(completion_rate AS FLOAT)) FROM seller_profiles WHERE completion_rate IS NOT NULL) AS avg_completion_rate,
    (SELECT AVG(CAST(rating_average AS FLOAT)) FROM seller_profiles WHERE rating_average IS NOT NULL) AS avg_rating,
    (SELECT TOP 1 gig_id FROM gigs WHERE seller_id = sp.seller_id AND is_active = 1 ORDER BY click_count DESC) AS best_performing_gig_id
FROM seller_profiles sp
JOIN users u ON sp.user_id = u.user_id
GO

-- Buyer dashboard view
CREATE VIEW vw_BuyerDashboard AS
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
GO

-- =====================================================
-- TRANSACTION VIEWS
-- =====================================================

-- Order details view
CREATE VIEW vw_OrderDetails AS
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
GO

-- =====================================================
-- COMMUNICATION VIEWS
-- =====================================================

-- Message threads view
CREATE VIEW vw_MessageThreads AS
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
GO

-- =====================================================
-- ANALYTICS VIEWS
-- =====================================================

-- Top sellers view
CREATE VIEW vw_TopSellers AS
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
    COALESCE((SELECT AVG(CAST(r.overall_rating AS FLOAT))
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
GO

-- Popular tags view
CREATE VIEW vw_PopularTags AS
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
GO

-- Seller analytics view
CREATE VIEW vw_SellerAnalytics AS
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
GO
