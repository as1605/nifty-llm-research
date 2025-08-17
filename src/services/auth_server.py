"""
Authentication server service for handling OAuth callbacks.
"""

import asyncio
import signal
import sys
from typing import Dict, Tuple
import webbrowser

from fastapi import FastAPI, HTTPException, Request
import uvicorn

from src.services.zerodha_service import ZerodhaService
from src.utils.logging import get_logger

logger = get_logger(__name__)


class AuthServerManager:
    """Context manager for managing the authentication server lifecycle."""
    
    def __init__(self):
        self.server_task = None
        self.server = None
        self.auth_complete = None
        self.user_id_result = None
        self._shutdown_complete = False
    
    async def __aenter__(self):
        """Start the authentication server."""
        logger.info("Starting authentication server...")
        self.user_id_result, self.auth_complete, self.server_task, self.server = await start_auth_server()
        logger.info("Authentication server started successfully")
        return self
    
    def is_server_running(self) -> bool:
        """Check if the server is still running."""
        if not self.server_task:
            return False
        return not self.server_task.done()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Ensure proper cleanup of the authentication server."""
        if self._shutdown_complete:
            return
            
        logger.info("Starting server shutdown process...")
        
        if self.server_task and not self.server_task.done():
            try:
                logger.info("Cancelling server task...")
                # Cancel the server task
                self.server_task.cancel()
                
                # Wait for graceful shutdown with timeout
                try:
                    await asyncio.wait_for(self.server_task, timeout=3.0)
                    logger.info("Server task completed gracefully")
                except asyncio.TimeoutError:
                    logger.warning("Server task did not complete within timeout")
                except asyncio.CancelledError:
                    # Expected when task is cancelled
                    logger.info("Server task was cancelled as expected")
                
                # Force stop uvicorn server
                if self.server and hasattr(self.server, 'should_exit'):
                    self.server.should_exit = True
                if self.server and hasattr(self.server, 'force_exit'):
                    self.server.force_exit = True
                
                # Give time for cleanup
                await asyncio.sleep(0.3)
                
            except Exception as e:
                logger.warning(f"Error during server cleanup: {e}")
        
        # Additional cleanup: ensure task is done
        if self.server_task and not self.server_task.done():
            logger.warning("Server task still running, forcing cleanup")
            try:
                self.server_task.cancel()
                # Don't wait again, just cancel
            except Exception as e:
                logger.warning(f"Error during forced cleanup: {e}")
        
        # Final cleanup: check if server is still running and force stop
        if self.server:
            try:
                if hasattr(self.server, 'should_exit'):
                    self.server.should_exit = True
                if hasattr(self.server, 'force_exit'):
                    self.server.force_exit = True
                # Additional uvicorn cleanup
                if hasattr(self.server, '_cleanup'):
                    self.server._cleanup()
            except Exception as e:
                logger.warning(f"Error during final server cleanup: {e}")
        
        self._shutdown_complete = True
        logger.info("Server shutdown process completed")
    
    async def cleanup(self):
        """Manual cleanup method for explicit server shutdown."""
        if not self._shutdown_complete:
            await self.__aexit__(None, None, None)
    
    def __del__(self):
        """Destructor to ensure cleanup if context manager is not used properly."""
        if self.server_task and not self.server_task.done():
            logger.warning("AuthServerManager destroyed without proper cleanup")
            try:
                self.server_task.cancel()
            except Exception:
                pass


async def start_auth_server() -> Tuple[Dict, asyncio.Event, asyncio.Task, uvicorn.Server]:
    """Start FastAPI server for OAuth callback and return user_id when authentication completes."""
    app = FastAPI()
    auth_complete = asyncio.Event()
    user_id_result = {"user_id": None, "error": None}
    zerodha_service = ZerodhaService()
    
    @app.get("/callback")
    async def callback(request: Request):
        """Handle OAuth callback from Zerodha."""
        request_token = request.query_params.get("request_token")
        
        if not request_token:
            error_msg = "No request token received"
            user_id_result["error"] = error_msg
            auth_complete.set()
            return {"error": error_msg}
        
        try:
            user_id = await zerodha_service.authenticate(request_token)
            user_id_result["user_id"] = user_id
            auth_complete.set()
            return {"success": True, "user_id": user_id, "message": "Authentication successful! You can close this tab."}
            
        except Exception as e:
            error_msg = f"Authentication failed: {e}"
            user_id_result["error"] = error_msg
            auth_complete.set()
            return {"error": error_msg}
    
    @app.get("/")
    async def root():
        return {"message": "Zerodha OAuth callback server is running"}
    
    # Add shutdown event handler for graceful shutdown
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Auth server shutting down gracefully")
    
    # Start server in background
    config = uvicorn.Config(app, host="localhost", port=8080, log_level="error")
    server = uvicorn.Server(config)
    
    async def run_server():
        try:
            await server.serve()
        except asyncio.CancelledError:
            # Handle graceful shutdown when cancelled
            logger.info("Auth server shutdown requested")
            try:
                # Give the server a moment to close connections
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                # If we get cancelled again during cleanup, just exit
                pass
        except Exception as e:
            logger.error(f"Auth server error: {e}")
        finally:
            logger.info("Auth server task completed")
    
    # Start server as background task
    server_task = asyncio.create_task(run_server())
    
    # Wait a moment for server to start
    await asyncio.sleep(1)
    
    return user_id_result, auth_complete, server_task, server


async def authenticate_user(quiet: bool = False) -> str:
    """Complete authentication flow and return user_id."""
    zerodha_service = ZerodhaService()
    
    # Set up signal handlers for graceful shutdown
    original_handlers = {}
    
    def signal_handler(signum, frame):
        if not quiet:
            print(f"\nReceived signal {signum}, shutting down gracefully...")
        # The context manager will handle cleanup
    
    try:
        # Register signal handlers for graceful shutdown
        for sig in [signal.SIGINT, signal.SIGTERM]:
            original_handlers[sig] = signal.signal(sig, signal_handler)
    except (OSError, ValueError):
        # Signal handling not available on this platform
        pass
    
    if not quiet:
        print("Starting Zerodha authentication...")
        print("=" * 60)
    
    try:
        # Use context manager for automatic server cleanup
        async with AuthServerManager() as auth_manager:
            # Generate and display login URL
            login_url = zerodha_service.get_login_url()
            if not quiet:
                print(f"Please click the following link to authenticate with Zerodha:")
                print(f"\n🔗 {login_url}\n")
            
            # Try to open browser automatically
            try:
                webbrowser.open(login_url)
                if not quiet:
                    print("✅ Browser opened automatically")
            except:
                if not quiet:
                    print("❌ Could not open browser automatically")
            
            if not quiet:
                print("Waiting for authentication to complete...")
                print("(The browser will redirect to localhost:8080 after login)")
            
            # Wait for authentication to complete
            try:
                await asyncio.wait_for(auth_manager.auth_complete.wait(), timeout=300.0)  # 5 minutes timeout
            except asyncio.TimeoutError:
                if not quiet:
                    print("Authentication timeout - no response received within 5 minutes")
                raise Exception("Authentication timeout - please try again")
            
            if not quiet:
                print("Authentication completed, shutting down server...")
        
        # Check for errors
        if auth_manager.user_id_result["error"]:
            raise Exception(auth_manager.user_id_result["error"])
        
        user_id = auth_manager.user_id_result["user_id"]
        if not quiet:
            print(f"✅ Authentication successful! User ID: {user_id}")
            print("=" * 60)
        
        return user_id
        
    finally:
        # Restore original signal handlers
        try:
            for sig, handler in original_handlers.items():
                signal.signal(sig, handler)
        except (OSError, ValueError):
            pass
