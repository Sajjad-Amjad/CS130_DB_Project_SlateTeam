from fastapi import APIRouter

from app.api import auth, users, categories, gigs, orders, offers, reviews, messages, search, notifications, payments

api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(gigs.router, prefix="/gigs", tags=["gigs"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(offers.router, prefix="/offers", tags=["offers"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])