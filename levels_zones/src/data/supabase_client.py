# In levels_zones/src/data/supabase_client.py

# Add this new method to save weekly analysis separately
def save_weekly_analysis(self, session_id: str, session: TradingSession) -> bool:
    """
    Save weekly analysis data to separate table
    
    Args:
        session_id: The trading session UUID
        session: TradingSession object with weekly data
        
    Returns:
        bool: Success status
    """
    try:
        if not session.weekly_data:
            logger.info("No weekly data to save")
            return True
            
        # Prepare weekly analysis data
        weekly_record = {
            'session_id': session_id,
            'ticker': session.ticker,
            'date': session.date.isoformat(),
            'ticker_id': session.ticker_id,
            'trend_direction': session.weekly_data.trend_direction.value,
            'internal_trend': session.weekly_data.internal_trend.value,
            'position_structure': float(session.weekly_data.position_structure),
            'eow_bias': session.weekly_data.eow_bias.value,
            'notes': session.weekly_data.notes
        }
        
        # Extract weekly levels if they exist
        # Check if weekly_data has price_levels attribute
        if hasattr(session.weekly_data, 'price_levels') and session.weekly_data.price_levels:
            levels = session.weekly_data.price_levels
            # Map first 4 levels to wl1-wl4
            for i, level in enumerate(levels[:4], 1):
                if level and level > 0:  # Only add non-zero levels
                    weekly_record[f'wl{i}'] = float(level)
        
        # Check if we need to update or insert
        existing = self.client.table('weekly_analysis')\
            .select("id")\
            .eq('session_id', session_id)\
            .execute()
        
        if existing.data:
            # Update existing record
            result = self.client.table('weekly_analysis')\
                .update(weekly_record)\
                .eq('session_id', session_id)\
                .execute()
            logger.info(f"Updated weekly analysis for session {session_id}")
        else:
            # Insert new record
            result = self.client.table('weekly_analysis')\
                .insert(weekly_record)\
                .execute()
            logger.info(f"Created weekly analysis for session {session_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error saving weekly analysis: {e}")
        return False


# Update the create_session method to also save weekly analysis
def create_session(self, session: TradingSession) -> Tuple[bool, Optional[str]]:
    """
    Create a new trading session in the database.
    
    Args:
        session: TradingSession object to save
        
    Returns:
        Tuple of (success: bool, session_id: Optional[str])
    """
    try:
        # Convert the session object to a dictionary for database insertion
        session_data = {
            'ticker': session.ticker,
            'ticker_id': session.ticker_id,
            'date': session.date.isoformat(),
            'is_live': session.is_live,
            'historical_date': session.historical_date.isoformat() if session.historical_date else None,
            'historical_time': session.historical_time.isoformat() if session.historical_time else None,
            'weekly_data': session.weekly_data.to_dict() if session.weekly_data else None,
            'daily_data': session.daily_data.to_dict() if session.daily_data else None,
            # Ensure all metrics are included
            'pre_market_price': float(session.pre_market_price) if session.pre_market_price else None,
            'atr_5min': float(session.atr_5min) if session.atr_5min else None,
            'atr_10min': float(session.atr_10min) if session.atr_10min else None,
            'atr_15min': float(session.atr_15min) if session.atr_15min else None,
            'daily_atr': float(session.daily_atr) if session.daily_atr else None,
            'atr_high': float(session.atr_high) if session.atr_high else None,
            'atr_low': float(session.atr_low) if session.atr_low else None
        }
        
        # Insert into trading_sessions table
        result = self.client.table('trading_sessions').insert(session_data).execute()
        
        if result.data and len(result.data) > 0:
            session_id = result.data[0]['id']
            logger.info(f"Created session {session.ticker_id} with ID: {session_id}")
            
            # Save price levels if any exist
            if session.m15_levels:
                self._save_price_levels(session_id, session.m15_levels)
            
            # Save weekly analysis to separate table
            if session.weekly_data:
                self.save_weekly_analysis(session_id, session)
            
            return True, session_id
        
        return False, None
        
    except APIError as e:
        logger.error(f"API error creating session: {e}")
        return False, None
    except Exception as e:
        logger.error(f"Unexpected error creating session: {e}")
        return False, None


# Similarly update the update_session method
def update_session(self, session: TradingSession) -> bool:
    """
    Update an existing trading session.
    
    Args:
        session: TradingSession object with updated data
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # First, get the session ID
        existing = self.client.table('trading_sessions')\
            .select("id")\
            .eq('ticker_id', session.ticker_id)\
            .execute()
        
        if not existing.data:
            logger.error(f"Session not found for update: {session.ticker_id}")
            return False
        
        session_id = existing.data[0]['id']
        
        # Prepare update data
        update_data = {
            'is_live': session.is_live,
            'historical_date': session.historical_date.isoformat() if session.historical_date else None,
            'historical_time': session.historical_time.isoformat() if session.historical_time else None,
            'weekly_data': session.weekly_data.to_dict() if session.weekly_data else None,
            'daily_data': session.daily_data.to_dict() if session.daily_data else None,
            # Include all metrics in update
            'pre_market_price': float(session.pre_market_price) if session.pre_market_price else None,
            'atr_5min': float(session.atr_5min) if session.atr_5min else None,
            'atr_10min': float(session.atr_10min) if session.atr_10min else None,
            'atr_15min': float(session.atr_15min) if session.atr_15min else None,
            'daily_atr': float(session.daily_atr) if session.daily_atr else None,
            'atr_high': float(session.atr_high) if session.atr_high else None,
            'atr_low': float(session.atr_low) if session.atr_low else None
        }
        
        # Update the session
        result = self.client.table('trading_sessions')\
            .update(update_data)\
            .eq('id', session_id)\
            .execute()
        
        # Update price levels (delete and re-insert for simplicity)
        if session.m15_levels:
            self._delete_price_levels(session_id)
            self._save_price_levels(session_id, session.m15_levels)
        
        # Update weekly analysis
        if session.weekly_data:
            self.save_weekly_analysis(session_id, session)
        
        logger.info(f"Updated session: {session.ticker_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating session {session.ticker_id}: {e}")
        return False