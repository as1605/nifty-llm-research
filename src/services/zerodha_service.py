"""
Zerodha Kite API service for authentication and trading operations.
"""

import asyncio
import base64
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

from cryptography.fernet import Fernet
from kiteconnect import KiteConnect

from src.config.settings import settings
from src.db.database import db, COLLECTIONS
from src.db.models import ZerodhaToken
from src.utils.logging import get_logger
from src.services.yfinance_service import YFinanceService

logger = get_logger(__name__)


class ZerodhaService:
    """Service for Zerodha Kite API operations."""
    
    def __init__(self):
        if not settings.zerodha_api_key or not settings.zerodha_api_secret:
            raise ValueError(
                "Zerodha API credentials not found. Please set ZERODHA_API_KEY and "
                "ZERODHA_API_SECRET in your .env file. See README_REBALANCING.md for setup instructions."
            )
        
        if not settings.encryption_key:
            raise ValueError(
                "Encryption key not found. Please set ENCRYPTION_KEY in your .env file. "
                "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        
        self.api_key = settings.zerodha_api_key
        self.api_secret = settings.zerodha_api_secret
        self.encryption_key = settings.encryption_key.encode()
        self.fernet = Fernet(self.encryption_key)
        self.kite = None
        self.redirect_url = "http://localhost:8080/callback"
        self.yfinance_service = YFinanceService()
        
    def _encrypt_token(self, token: str) -> str:
        """Encrypt access token for storage."""
        return self.fernet.encrypt(token.encode()).decode()
    
    def _decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt access token from storage."""
        return self.fernet.decrypt(encrypted_token.encode()).decode()
    
    async def get_stored_token(self, user_id: str) -> Optional[str]:
        """Get stored access token for user."""
        token_doc = db[COLLECTIONS["zerodha_tokens"]].find_one({
            "user_id": user_id,
            "is_active": True
        })
        
        if not token_doc:
            return None
            
        try:
            # Decrypt the token
            decrypted_token = self._decrypt_token(token_doc["encrypted_access_token"])
            
            # Test if token is valid by making a simple API call
            test_kite = KiteConnect(api_key=self.api_key)
            test_kite.set_access_token(decrypted_token)
            test_kite.profile()  # This will raise an exception if token is invalid
            
            logger.info(f"Valid access token found for user {user_id}")
            return decrypted_token
            
        except Exception as e:
            logger.warning(f"Stored token for user {user_id} is invalid: {e}")
            # Mark token as inactive
            db[COLLECTIONS["zerodha_tokens"]].update_one(
                {"user_id": user_id},
                {"$set": {"is_active": False}}
            )
            return None
    
    async def store_token(self, user_id: str, access_token: str):
        """Store encrypted access token in database."""
        encrypted_token = self._encrypt_token(access_token)
        
        # Deactivate any existing tokens for this user
        db[COLLECTIONS["zerodha_tokens"]].update_many(
            {"user_id": user_id},
            {"$set": {"is_active": False}}
        )
        
        # Store new token
        token_doc = ZerodhaToken(
            user_id=user_id,
            encrypted_access_token=encrypted_token,
            created_time=datetime.now(timezone.utc),
            is_active=True
        )
        
        db[COLLECTIONS["zerodha_tokens"]].insert_one(token_doc.model_dump(exclude={"id"}))
        logger.info(f"Access token stored for user {user_id}")
    
    def get_login_url(self) -> str:
        """Generate Zerodha login URL."""
        kite = KiteConnect(api_key=self.api_key)
        return kite.login_url()
    
    async def authenticate(self, request_token: str) -> str:
        """Exchange request token for access token."""
        kite = KiteConnect(api_key=self.api_key)
        
        try:
            data = kite.generate_session(request_token, api_secret=self.api_secret)
            access_token = data["access_token"]
            user_id = data["user_id"]
            
            # Store the token
            await self.store_token(user_id, access_token)
            
            # Set up the kite instance
            self.kite = kite
            kite.set_access_token(access_token)
            
            logger.info(f"Authentication successful for user {user_id}")
            return user_id
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise HTTPException(status_code=400, detail=f"Authentication failed: {e}")
    
    async def get_authenticated_kite(self, user_id: str) -> KiteConnect:
        """Get authenticated KiteConnect instance."""
        access_token = await self.get_stored_token(user_id)
        
        if not access_token:
            raise ValueError(f"No valid access token found for user {user_id}. Please re-authenticate.")
        
        kite = KiteConnect(api_key=self.api_key)
        kite.set_access_token(access_token)
        return kite
    
    async def get_portfolio_summary(self, user_id: str) -> Dict:
        """Get complete portfolio summary including holdings, positions, and funds."""
        kite = await self.get_authenticated_kite(user_id)
        
        try:
            # Get holdings
            holdings = kite.holdings()
            
            # Get positions
            positions = kite.positions()
            
            # Get funds/margins
            margins = kite.margins()
            
            # Calculate total portfolio value
            # Holdings: last_price * opening_quantity
            holdings_value = sum(
                float(h.get('last_price') or 0.0) * int(h.get('opening_quantity') or 0)
                for h in holdings
            )
            # Positions (net): last_price * quantity * multiplier
            positions_value = sum(
                float(p.get("last_price") or 0.0) * int(p.get("quantity") or 0) * int(p.get("multiplier") or 1)
                for p in positions.get("net", [])
            )

            available_cash = float(margins['equity']['net'])
            
            total_value = holdings_value + positions_value + available_cash
            
            return {
                'holdings': holdings,
                'positions': positions,
                'margins': margins,
                'total_value': total_value,
                'holdings_value': holdings_value,
                'positions_value': positions_value,
                'available_cash': available_cash
            }
            
        except Exception as e:
            logger.error(f"Failed to get portfolio summary: {e}")
            raise
    
    async def place_order(self, user_id: str, variety: str, exchange: str, 
                         tradingsymbol: str, transaction_type: str, quantity: int,
                         product: str, order_type: str, price: Optional[float] = None) -> str:
        """Place an order on Zerodha."""
        kite = await self.get_authenticated_kite(user_id)
        
        try:
            order_params = {
                'variety': variety,
                'exchange': exchange,
                'tradingsymbol': tradingsymbol,
                'transaction_type': transaction_type,
                'quantity': quantity,
                'product': product,
                'order_type': order_type
            }
            
            if price:
                order_params['price'] = price
                
            order_id = kite.place_order(**order_params)
            logger.info(f"Order placed successfully: {order_id}")
            return order_id
            
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise
    
    async def get_instrument_token(self, user_id: str, tradingsymbol: str, exchange: str = "NSE") -> Optional[int]:
        """Get instrument token for a given symbol."""
        kite = await self.get_authenticated_kite(user_id)
        
        try:
            instruments = kite.instruments(exchange)
            for instrument in instruments:
                if instrument['tradingsymbol'] == tradingsymbol:
                    return instrument['instrument_token']
            return None
            
        except Exception as e:
            logger.error(f"Failed to get instrument token: {e}")
            raise
    
    async def get_ltp(self, user_id: str, instruments: List[str]) -> Dict:
        """Get Last Traded Price (LTP) for given instruments using the yfinance service.

        Input instruments are expected as ["NSE:RELIANCE", "BSE:SBIN", ...].
        Returns a dict like {"NSE:RELIANCE": {"last_price": 1234.5}, ...}.
        """
        results: Dict[str, Dict[str, float]] = {}

        def to_yf_symbol(instrument: str) -> Optional[str]:
            try:
                exchange, symbol = instrument.split(":", 1)
            except ValueError:
                return None
            exchange = exchange.upper().strip()
            # For NSE stocks, just return the symbol (yfinance service will add .NS)
            # For BSE stocks, return with .BO suffix
            if exchange == "NSE":
                return symbol.strip()
            elif exchange == "BSE":
                return f"{symbol.strip()}.BO"
            else:
                return None

        for inst in instruments:
            yf_symbol = to_yf_symbol(inst)
            if not yf_symbol:
                logger.warning(f"Invalid instrument format: {inst}")
                continue
                
            try:
                # Use the yfinance service to get LTP
                ltp = self.yfinance_service.get_stock_ltp(yf_symbol)
                if ltp is not None:
                    results[inst] = {"last_price": ltp}
                    logger.debug(f"Successfully fetched LTP for {inst} ({yf_symbol}): ₹{ltp}")
                else:
                    logger.warning(f"No LTP available for {inst} ({yf_symbol})")
            except Exception as e:
                logger.warning(f"yfinance LTP fetch failed for {inst} ({yf_symbol}): {e}")
                continue

        return results


# Authentication functions are now in src.services.auth_server
# Import and re-export for backward compatibility
async def authenticate_user(quiet: bool = False) -> str:
    """Complete authentication flow and return user_id."""
    from src.services.auth_server import authenticate_user as auth_user
    return await auth_user(quiet) 