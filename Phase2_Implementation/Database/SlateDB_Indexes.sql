USE [SlateDB2];
GO

-- Drop existing indexes if they exist
IF EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Gigs_RankingScore' AND object_id = OBJECT_ID('gigs'))
    DROP INDEX IX_Gigs_RankingScore ON gigs;

IF EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Gigs_CategoryId' AND object_id = OBJECT_ID('gigs'))
    DROP INDEX IX_Gigs_CategoryId ON gigs;

IF EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Orders_BuyerId' AND object_id = OBJECT_ID('orders'))
    DROP INDEX IX_Orders_BuyerId ON orders;

IF EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Orders_SellerId' AND object_id = OBJECT_ID('orders'))
    DROP INDEX IX_Orders_SellerId ON orders;

IF EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Messages_ConversationId' AND object_id = OBJECT_ID('messages'))
    DROP INDEX IX_Messages_ConversationId ON messages;

IF EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_GigTags_TagId' AND object_id = OBJECT_ID('gig_tags'))
    DROP INDEX IX_GigTags_TagId ON gig_tags;

IF EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Notifications_UserId_IsRead' AND object_id = OBJECT_ID('notifications'))
    DROP INDEX IX_Notifications_UserId_IsRead ON notifications;


-- Gig ranking and search indexes
CREATE INDEX IX_Gigs_RankingScore ON gigs (ranking_score DESC);

CREATE INDEX IX_Gigs_CategoryId ON gigs (category_id);

-- Order management indexes
CREATE INDEX IX_Orders_BuyerId ON orders (buyer_id);

CREATE INDEX IX_Orders_SellerId ON orders (seller_id);

-- Communication indexes
CREATE INDEX IX_Messages_ConversationId ON messages (conversation_id);

-- Tag system indexes
CREATE INDEX IX_GigTags_TagId ON gig_tags (tag_id);

-- Notification system indexes
CREATE INDEX IX_Notifications_UserId_IsRead ON notifications (user_id, is_read);

PRINT 'All indexes created successfully in SlateDB2!';
GO