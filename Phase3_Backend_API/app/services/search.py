from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, asc, func

from app.models.gig import Gig, GigPackage
from app.models.user import User, SellerProfile
from app.models.category import Category
from app.models.tag import Tag, GigTag

class SearchService:
    @staticmethod
    def search_gigs(
        db: Session,
        query: str,
        category_id: Optional[int] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        delivery_time: Optional[int] = None,
        seller_level: Optional[str] = None,
        sort_by: str = "relevance",
        skip: int = 0,
        limit: int = 20
    ) -> List[Gig]:
        """Search for gigs with various filters."""
        gig_query = db.query(Gig).filter(Gig.is_active == True)
        
        # Text search
        search_conditions = or_(
            Gig.title.ilike(f"%{query}%"),
            Gig.description.ilike(f"%{query}%"),
            Gig.search_tags.ilike(f"%{query}%")
        )
        gig_query = gig_query.filter(search_conditions)
        
        # Category filter
        if category_id:
            gig_query = gig_query.filter(Gig.category_id == category_id)
        
        # Price filters
        if min_price or max_price:
            price_subquery = db.query(
                GigPackage.gig_id,
                func.min(GigPackage.price).label('min_price')
            ).filter(GigPackage.is_active == True).group_by(GigPackage.gig_id).subquery()
            
            gig_query = gig_query.join(price_subquery, Gig.gig_id == price_subquery.c.gig_id)
            
            if min_price:
                gig_query = gig_query.filter(price_subquery.c.min_price >= min_price)
            if max_price:
                gig_query = gig_query.filter(price_subquery.c.min_price <= max_price)
        
        # Delivery time filter
        if delivery_time:
            delivery_subquery = db.query(
                GigPackage.gig_id,
                func.min(GigPackage.delivery_time).label('min_delivery')
            ).filter(GigPackage.is_active == True).group_by(GigPackage.gig_id).subquery()
            
            gig_query = gig_query.join(delivery_subquery, Gig.gig_id == delivery_subquery.c.gig_id)
            gig_query = gig_query.filter(delivery_subquery.c.min_delivery <= delivery_time)
        
        # Seller level filter
        if seller_level:
            gig_query = gig_query.join(SellerProfile, Gig.seller_id == SellerProfile.seller_id)
            gig_query = gig_query.filter(SellerProfile.account_level == seller_level)
        
        # Sorting
        if sort_by == "relevance":
            # Create a relevance score based on text matching
            gig_query = gig_query.order_by(desc(Gig.ranking_score))
        elif sort_by == "price":
            gig_query = gig_query.order_by(asc(Gig.gig_id))  # Would need price subquery
        elif sort_by == "delivery_time":
            gig_query = gig_query.order_by(asc(Gig.gig_id))  # Would need delivery subquery
        elif sort_by == "rating":
            gig_query = gig_query.order_by(desc(Gig.ranking_score))
        
        return gig_query.offset(skip).limit(limit).all()

    @staticmethod
    def search_sellers(
        db: Session,
        query: str,
        category_id: Optional[int] = None,
        min_rating: Optional[float] = None,
        account_level: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[User]:
        """Search for sellers."""
        seller_query = db.query(User).join(SellerProfile, User.user_id == SellerProfile.user_id)
        
        # Text search
        search_conditions = or_(
            User.full_name.ilike(f"%{query}%"),
            SellerProfile.professional_title.ilike(f"%{query}%"),
            SellerProfile.description.ilike(f"%{query}%")
        )
        seller_query = seller_query.filter(search_conditions)
        
        # Category filter (sellers who have gigs in this category)
        if category_id:
            gig_subquery = db.query(Gig.seller_id).filter(
                Gig.category_id == category_id,
                Gig.is_active == True
            ).distinct().subquery()
            
            seller_query = seller_query.filter(SellerProfile.seller_id.in_(gig_subquery))
        
        # Rating filter
        if min_rating:
            seller_query = seller_query.filter(SellerProfile.rating_average >= min_rating)
        
        # Account level filter
        if account_level:
            seller_query = seller_query.filter(SellerProfile.account_level == account_level)
        
        # Order by rating
        seller_query = seller_query.order_by(desc(SellerProfile.rating_average))
        
        return seller_query.offset(skip).limit(limit).all()

    @staticmethod
    def get_search_suggestions(db: Session, query: str, limit: int = 10) -> List[str]:
        """Get search suggestions based on query."""
        suggestions = []
        
        # Get suggestions from gig titles
        gig_titles = db.query(Gig.title).filter(
            Gig.title.ilike(f"%{query}%"),
            Gig.is_active == True
        ).limit(limit // 2).all()
        
        suggestions.extend([title[0] for title in gig_titles])
        
        # Get suggestions from tags
        tags = db.query(Tag.name).filter(
            Tag.name.ilike(f"%{query}%")
        ).order_by(desc(Tag.frequency)).limit(limit // 2).all()
        
        suggestions.extend([tag[0] for tag in tags])
        
        return list(set(suggestions))[:limit]

    @staticmethod
    def get_search_filters(db: Session, category_id: Optional[int] = None) -> Dict[str, Any]:
        """Get available search filters."""
        filters = {}
        
        # Get categories
        if category_id:
            subcategories = db.query(Category).filter(
                Category.parent_category_id == category_id,
                Category.is_active == True
            ).all()
            filters["subcategories"] = [
                {"id": cat.category_id, "name": cat.name} for cat in subcategories
            ]
        else:
            categories = db.query(Category).filter(
                Category.parent_category_id.is_(None),
                Category.is_active == True
            ).order_by(Category.display_order).all()
            filters["categories"] = [
                {"id": cat.category_id, "name": cat.name} for cat in categories
            ]
        
        # Get seller levels
        filters["seller_levels"] = [
            {"value": "new", "label": "New Seller"},
            {"value": "level_1", "label": "Level 1"},
            {"value": "level_2", "label": "Level 2"},
            {"value": "top_rated", "label": "Top Rated"}
        ]
        
        # Get price ranges (could be dynamic based on data)
        filters["price_ranges"] = [
            {"min": 0, "max": 25, "label": "Under $25"},
            {"min": 25, "max": 50, "label": "$25 - $50"},
            {"min": 50, "max": 100, "label": "$50 - $100"},
            {"min": 100, "max": 250, "label": "$100 - $250"},
            {"min": 250, "max": None, "label": "$250+"}
        ]
        
        # Get delivery times
        filters["delivery_times"] = [
            {"value": 1, "label": "1 Day"},
            {"value": 3, "label": "Up to 3 Days"},
            {"value": 7, "label": "Up to 1 Week"},
            {"value": 14, "label": "Up to 2 Weeks"},
            {"value": 30, "label": "Up to 1 Month"}
        ]
        
        return filters