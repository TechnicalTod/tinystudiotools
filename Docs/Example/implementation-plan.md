# Support Ticket System - Implementation Plan

## Phase 1: Database Setup

1. **Create Database Models**

   - Implement SupportTicket model in `/db/models/support_ticket.py` using SQLAlchemy 2.0 syntax with type annotations
   - Implement ReportCooldown model in `/db/models/report_cooldown.py` using SQLAlchemy 2.0 syntax
   - Update `/db/models/__init__.py` to include new models
   - Ensure model definitions include appropriate indexes for query performance

2. **Database Migration**
   - Option A: Create Alembic migration using `alembic revision --autogenerate -m "Create support ticket tables"`
   - Option B: If Alembic migrations have issues, create a direct SQL script in `scripts/create_support_tables.py` that:
     - Connects directly to Neon PostgreSQL using psycopg
     - Creates tables with appropriate constraints and indexes
     - Includes trigger functions for automatic timestamp updates
     - Verifies the tables were created successfully
   - Test schema on development environment
   - Apply to production database when ready

## Phase 2: Repository Implementation

1. **Create Repository Classes**

   - Implement SupportTicketRepository in `/db/repositories/support_ticket_repository.py` extending BaseRepository
   - Implement ReportCooldownRepository in `/db/repositories/report_cooldown_repository.py` extending BaseRepository
   - Implement both synchronous and asynchronous access patterns
   - Include appropriate indexes and query optimizations for Neon.tech
   - Update `/db/repositories/__init__.py` to include new repositories

2. **Direct SQL Fallback**

   - Implement raw SQL query options for critical performance paths
   - Create helper methods for common operations that might need optimization
   - Ensure proper parameter sanitization for all raw SQL

3. **Unit Tests**
   - Write tests for SupportTicket repository methods
   - Write tests for ReportCooldown repository methods
   - Ensure all CRUD operations work correctly
   - Test connection resilience with Neon auto-suspend feature

## Phase 3: Middleware Implementation

1. **Create Cooldown Middleware**

   - Create new file `platforms/telegram/middleware/cooldown.py` with the cooldown middleware function:
     ```python
     async def check_cooldown_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE):
         """Check if user is currently in a cooldown period for specific commands"""
         # Implementation logic here
     ```
   - Implement logic to check if user can submit a new report
   - Add cooldown information to context for handlers to use
   - Add logging for cooldown enforcement

2. **Integrate with Bot Application**

   - Add import to `platforms/telegram/middleware/__init__.py`
   - Register middleware in proper priority in `create_telegram_bot` function:
     ```python
     # Add after whitelist middleware but before command analytics
     application.add_handler(MessageHandler(filters.COMMAND, check_cooldown_middleware), group=-2)
     ```
   - Ensure middleware only processes command messages

3. **Environment Variables**
   - TELEGRAM_ADMIN_CHANNEL_ID="-1002340417841" - this will be the channel that tickets are sent to
   - Add `REPORT_COOLDOWN_SECONDS` variable to `.env` file (default: 3600)
   - Configure environment variable loading in Settings class
   - Document environment variables in README

## Phase 4: Handler Implementation

1. **Create Support Handlers Module**

   - Create new file `platforms/telegram/handlers/support_handlers.py`
   - Implement `SupportHandlers` class with report and admin methods
   - Add to handler imports in `__init__.py`

2. **Report Command**

   - Implement `handle_report` method for processing user reports
   - Add input validation and sanitization
   - Implement database operations for storing tickets
   - Send confirmation to user and notification to dev channel

3. **Admin Commands**
   - Implement `handle_tickets` for listing recent tickets
   - Implement `handle_close_ticket` for changing ticket status
   - Add admin validation to restrict access
   - Add commands to client handler registration
   - Implement new unified `handle_ticket` command with parser for multiple actions:
     - `open` - Reopen closed tickets
     - `close` - Close open tickets
     - `list` - List tickets with filtering options

## Phase 5: Testing & Integration

1. **Middleware Testing**

   - Test cooldown middleware in isolation
   - Verify correct cooldown period enforcement
   - Test interaction with different commands
   - Validate context data is properly set

2. **Handler Testing**

   - Test report submission functionality
   - Test admin command access control
   - Verify database operations work correctly
   - Test input sanitization and validation

3. **End-to-End Testing**
   - Test full user flow from report submission to admin review
   - Test cooldown enforcement between reports
   - Verify channel notifications are correctly formatted
   - Test error handling and edge cases

## Phase 6: Documentation & Deployment

1. **User Documentation**

   - Document the `/report` command and expected format
   - Include information about cooldown periods
   - Update help commands to reference support ticket system

2. **Admin Documentation**

   - Document admin commands for ticket management
   - Create examples for common ticket workflows
   - Provide troubleshooting information

3. **Deployment**
   - Deploy to staging environment
   - Test in production-like environment
   - Roll out to production

## Implementation Steps for Cooldown Middleware

### Step 1: Create the Cooldown Middleware File

Create a new file `platforms/telegram/middleware/cooldown.py` with the following content:

```python
"""Middleware for managing command cooldowns"""

import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from db.session import get_async_db_session
from db.repositories.report_cooldown_repository import ReportCooldownRepository

logger = logging.getLogger(__name__)

async def check_cooldown_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Middleware to check if a user is currently in a cooldown period for specific commands.
    Adds cooldown information to the context for handlers to use.
    """
    # Only process for command messages
    if not (update.message and update.message.text and update.message.text.startswith("/")):
        return True

    # Extract base command
    command = update.message.text.split()[0].split("@")[0][1:]

    # Only check cooldowns for commands that have them
    cooldown_commands = ["report"]
    if command not in cooldown_commands:
        return True

    # Get services from context
    if not (hasattr(context, "bot_data") and "services" in context.bot_data):
        logger.warning("Could not check cooldown: services not found in context.bot_data")
        return True

    services = context.bot_data["services"]
    user_id = update.effective_user.id
    settings = context.bot_data.get("settings")
    cooldown_seconds = settings.report_cooldown_seconds if settings else 3600

    # Check for cooldown in database
    conn = await services.db.get_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT last_reported_at FROM report_cooldowns WHERE user_id = %s",
                (user_id,)
            )
            row = await cur.fetchone()

            if row:
                last_report = row[0]
                current_time = datetime.utcnow()

                # Calculate remaining cooldown time
                elapsed_seconds = (current_time - last_report).total_seconds()
                remaining_seconds = max(0, cooldown_seconds - elapsed_seconds)

                # Add cooldown info to context for the handler to use
                context.cooldown_info = {
                    "in_cooldown": remaining_seconds > 0,
                    "remaining_seconds": remaining_seconds,
                    "cooldown_minutes": int(remaining_seconds / 60)
                }

                if remaining_seconds > 0:
                    logger.info(f"User {user_id} attempted to use /{command} while in cooldown ({int(remaining_seconds)} seconds remaining)")
            else:
                # No cooldown record exists
                context.cooldown_info = {
                    "in_cooldown": False,
                    "remaining_seconds": 0,
                    "cooldown_minutes": 0
                }
    finally:
        await services.db.release_connection(conn)

    # Always continue processing
    return True
```

### Step 2: Update the Bot Configuration

Modify the `create_telegram_bot` function in `platforms/telegram/bot.py`:

```python
def create_telegram_bot(settings: Settings, services: Services) -> Application:
    """Create and configure the Telegram bot"""
    setup_logging()

    # Configure request with longer timeouts
    req = HTTPXRequest(
        connect_timeout=30,
        read_timeout=30,
        write_timeout=30,
    )

    application = Application.builder().token(settings.telegram_token).request(req).build()

    # Store services and settings in the bot context for access by middleware
    application.bot_data["services"] = services
    application.bot_data["settings"] = settings

    # Initialize handlers
    legacy_handlers = TelegramHandlers(services)
    telegram_client = TelegramClient(services, settings)

    # Register middleware in proper priority order:
    # 1. Timing middleware (first, to track total time)
    application.add_handler(MessageHandler(filters.ALL, request_timing_middleware), group=-5)

    # 2. Message storage middleware (store all messages regardless of whitelist)
    application.add_handler(MessageHandler(filters.ALL, store_message_middleware), group=-4)

    # 3. Whitelist middleware (access control, after storage)
    application.add_handler(MessageHandler(filters.ALL, whitelist_middleware), group=-3)

    # 4. Cooldown middleware (after whitelist, before analytics)
    application.add_handler(MessageHandler(filters.COMMAND, check_cooldown_middleware), group=-2)

    # 5. Command analytics middleware (only track whitelisted commands)
    application.add_handler(MessageHandler(filters.COMMAND, command_analytics_middleware), group=-1)

    # Rest of the handler registration...
```

### Step 3: Test the Middleware

1. Start the bot with a short cooldown period for testing
2. Submit a `/report` command
3. Try to submit another report within the cooldown period
4. Verify cooldown information is shown to the user
5. Wait for cooldown to expire and verify reports are accepted again

## Timeline

| Phase                      | Estimated Time | Dependencies              | Status     |
| -------------------------- | -------------- | ------------------------- | ---------- |
| Database Setup             | 1 day          | None                      | ⏳ Pending |
| Repository Implementation  | 1 day          | Database Setup            | ⏳ Pending |
| Middleware Implementation  | 1 day          | Repository Implementation | ⏳ Pending |
| Handler Implementation     | 1 day          | Middleware Implementation | ⏳ Pending |
| Testing & Integration      | 2 days         | Handler Implementation    | ⏳ Pending |
| Documentation & Deployment | 1 day          | Testing & Integration     | ⏳ Pending |

**Total Estimated Time**: 7 working days

## Success Criteria

- All database tables and models are correctly implemented
- Cooldown system successfully limits report frequency
- Reports are properly stored and displayed to admins
- Admin commands work as expected for ticket management
- All tests pass

## Notes on Database Deployment

If you encounter issues with Alembic migrations on Neon.tech, follow these steps:

1. **Create a Direct SQL Script**:

   - Develop a standalone Python script similar to `scripts/create_tasks_table.py`
   - Use the `psycopg` library for direct connection to the database
   - Include verification steps to confirm table creation
   - Add proper error handling and reporting

2. **Run the Script**:

   - Execute the script from the project root: `python scripts/create_support_tables.py`
   - Verify in the console that the tables were created successfully
   - Check in the Neon.tech dashboard that tables appear in the database

3. **Document the Schema Change**:
   - Update migration history in a comment if using this approach
   - Create a corresponding Alembic migration that would be a no-op if the tables exist
   - Ensure the schema is properly documented in the code
