# Support Ticket System - Backend Blueprint

## Database Models

### Support Ticket Model

```python
from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, Text, String, Index, func
from sqlalchemy.types import Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class SupportTicket(Base):
    """Model for storing user support tickets"""

    __tablename__ = "support_tickets"

    # Basic ticket information
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # User information
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(100))

    # Ticket content
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Ticket metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=None, onupdate=datetime.utcnow
    )
    status: Mapped[str] = mapped_column(
        String(20), default="open", nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<SupportTicket(id={self.id}, user_id={self.user_id}, status='{self.status}')>"
```

### Report Cooldown Model

```python
from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, func
from sqlalchemy.types import DateTime
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class ReportCooldown(Base):
    """Model for tracking user report cooldowns"""

    __tablename__ = "report_cooldowns"

    # User identifier (primary key)
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # Timestamp of last report
    last_reported_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<ReportCooldown(user_id={self.user_id})>"
```

## Repository Classes

### Support Ticket Repository

```python
class SupportTicketRepository(BaseRepository[SupportTicket]):
    """Repository for support ticket operations"""

    async def create_ticket(
        self,
        user_id: int,
        username: Optional[str],
        message: str,
    ) -> SupportTicket:
        """Create a new support ticket"""
        ticket = SupportTicket(
            user_id=user_id,
            username=username,
            message=message,
            status="open"
        )

        self.session.add(ticket)
        await self.session.flush()
        await self.session.refresh(ticket)

        return ticket

    async def get_recent_tickets(self, limit: int = 10) -> List[SupportTicket]:
        """Get recent support tickets ordered by creation date"""
        stmt = select(SupportTicket).order_by(
            SupportTicket.created_at.desc()
        ).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_ticket_by_id(self, ticket_id: int) -> Optional[SupportTicket]:
        """Get a specific ticket by ID"""
        stmt = select(SupportTicket).where(SupportTicket.id == ticket_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def close_ticket(self, ticket_id: int) -> Optional[SupportTicket]:
        """Mark a ticket as closed"""
        ticket = await self.get_ticket_by_id(ticket_id)

        if ticket:
            ticket.status = "closed"
            self.session.add(ticket)
            await self.session.flush()
            await self.session.refresh(ticket)

        return ticket

    async def get_user_tickets(self, user_id: int, limit: int = 5) -> List[SupportTicket]:
        """Get recent tickets from a specific user"""
        stmt = select(SupportTicket).where(
            SupportTicket.user_id == user_id
        ).order_by(
            SupportTicket.created_at.desc()
        ).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def reopen_ticket(self, ticket_id: int) -> Optional[SupportTicket]:
        """Reopen a closed ticket"""
        ticket = await self.get_ticket_by_id(ticket_id)

        if ticket:
            if ticket.status == "closed":
                ticket.status = "open"
                ticket.updated_at = datetime.utcnow()
                self.session.add(ticket)
                await self.session.flush()
                await self.session.refresh(ticket)
            return ticket

        return None
```

### Report Cooldown Repository

```python
class ReportCooldownRepository(BaseRepository[ReportCooldown]):
    """Repository for user report cooldown operations"""

    async def get_user_cooldown(self, user_id: int) -> Optional[ReportCooldown]:
        """Get a user's cooldown record if it exists"""
        stmt = select(ReportCooldown).where(ReportCooldown.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_or_update_cooldown(self, user_id: int) -> ReportCooldown:
        """Create a new cooldown record or update existing one"""
        cooldown = await self.get_user_cooldown(user_id)

        if cooldown:
            # Update existing record
            cooldown.last_reported_at = datetime.utcnow()
            self.session.add(cooldown)
        else:
            # Create new record
            cooldown = ReportCooldown(
                user_id=user_id,
                last_reported_at=datetime.utcnow()
            )
            self.session.add(cooldown)

        await self.session.flush()
        await self.session.refresh(cooldown)
        return cooldown

    async def is_in_cooldown(self, user_id: int, cooldown_seconds: int = 3600) -> Tuple[bool, int]:
        """
        Check if user is in cooldown period and return cooldown info

        Returns:
            Tuple[bool, int]: (is_in_cooldown, remaining_seconds)
        """
        cooldown = await self.get_user_cooldown(user_id)

        if not cooldown:
            return False, 0

        elapsed_seconds = (datetime.utcnow() - cooldown.last_reported_at).total_seconds()
        remaining_seconds = max(0, cooldown_seconds - elapsed_seconds)

        return remaining_seconds > 0, int(remaining_seconds)
```

## Handler Implementation

### Support Handlers

```python
class SupportHandlers:
    """Handler for support ticket functionality"""

    def __init__(self, services: Services, settings: Settings):
        self.services = services
        self.settings = settings
        self.channel_id = settings.support_channel_id

    async def handle_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /report command to submit support tickets"""
        user = update.effective_user
        msg = ' '.join(context.args) if context.args else ""

        # Basic validation
        if not msg:
            await update.message.reply_text("Please include a message with your report.")
            return

        # Sanitize input (limit length, remove problematic characters)
        msg = msg.strip()
        if len(msg) > 1000:  # Reasonable limit
            msg = msg[:997] + "..."

        # Remove potential markdown or HTML formatting
        msg = msg.replace('_', '\\_').replace('*', '\\*').replace('`', '\\`')

        # Check cooldown (handled by middleware)
        if hasattr(context, "cooldown_info") and context.cooldown_info["in_cooldown"]:
            minutes = context.cooldown_info["cooldown_minutes"]
            await update.message.reply_text(
                f"You've recently submitted a report. Please wait about {minutes} minutes before sending another."
            )
            return

        async with get_async_db_session() as session:
            # Create repositories
            ticket_repo = SupportTicketRepository(session)
            cooldown_repo = ReportCooldownRepository(session)

            # Insert ticket
            ticket = await ticket_repo.create_ticket(
                user_id=user.id,
                username=user.username,
                message=msg
            )

            # Update cooldown
            await cooldown_repo.create_or_update_cooldown(user.id)

            # Commit changes
            await session.commit()

            # Send to dev channel
            await context.bot.send_message(
                chat_id=self.channel_id,
                text=f"🛠 New Ticket #{ticket.id}\nFrom: @{user.username or user.id}\nMessage: {msg}"
            )

            # Confirm to user
            await update.message.reply_text("Thank you, your report has been submitted.")

            # Log analytics
            try:
                await self.services.analytics.track_event(
                    "support_ticket_created",
                    {
                        "user_id": user.id,
                        "username": user.username,
                        "ticket_id": ticket.id,
                        "platform": "telegram"
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to track analytics for support ticket: {e}")

    async def handle_tickets(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to list recent tickets"""
        # Check if user is admin
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("This command is only available to admins.")
            return

        # Parse limit
        limit = 10
        if context.args and context.args[0].isdigit():
            limit = min(int(context.args[0]), 50)  # Limit to 50 max

        async with get_async_db_session() as session:
            ticket_repo = SupportTicketRepository(session)
            tickets = await ticket_repo.get_recent_tickets(limit)

            if not tickets:
                await update.message.reply_text("No tickets found.")
                return

            report = "📋 Recent Support Tickets:\n\n"
            for ticket in tickets:
                msg_preview = ticket.message[:50] + ("..." if len(ticket.message) > 50 else "")
                report += f"ID: {ticket.id} | Status: {ticket.status}\n"
                report += f"From: @{ticket.username or ticket.user_id} | {ticket.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                report += f"Message: {msg_preview}\n\n"

            await update.message.reply_text(report)

    async def handle_close_ticket(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to close a ticket"""
        # Check if user is admin
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("This command is only available to admins.")
            return

        # Validate ticket ID
        if not context.args or not context.args[0].isdigit():
            await update.message.reply_text("Please provide a valid ticket ID: /close_ticket <id>")
            return

        ticket_id = int(context.args[0])

        async with get_async_db_session() as session:
            ticket_repo = SupportTicketRepository(session)
            ticket = await ticket_repo.close_ticket(ticket_id)
            await session.commit()

            if ticket:
                await update.message.reply_text(f"Ticket #{ticket_id} has been closed.")

                # Log the action
                logger.info(f"Admin {update.effective_user.id} closed ticket #{ticket_id}")
            else:
                await update.message.reply_text(f"Ticket #{ticket_id} not found.")
```

## Middleware Implementation

### Cooldown Middleware

```python
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

    # Skip checks if user is an admin
    if is_admin(update.effective_user.id):
        context.cooldown_info = {
            "in_cooldown": False,
            "remaining_seconds": 0,
            "cooldown_minutes": 0,
        }
        return True

    # Get settings from context
    settings = context.bot_data.get("settings")
    cooldown_seconds = settings.report_cooldown_seconds if settings else 3600

    try:
        async with get_async_db_session() as session:
            cooldown_repo = ReportCooldownRepository(session)

            # Check cooldown status
            in_cooldown, remaining_seconds = await cooldown_repo.is_in_cooldown(
                update.effective_user.id, cooldown_seconds
            )

            # Add cooldown info to context for the handler to use
            context.cooldown_info = {
                "in_cooldown": in_cooldown,
                "remaining_seconds": remaining_seconds,
                "cooldown_minutes": math.ceil(remaining_seconds / 60) if remaining_seconds > 0 else 0,
            }

            if in_cooldown:
                logger.info(
                    f"User {update.effective_user.id} attempted to use /{command} "
                    f"while in cooldown ({remaining_seconds} seconds remaining)"
                )

    except Exception as e:
        # Log error but continue processing to avoid breaking bot functionality
        logger.error(f"Error checking command cooldown: {e}", exc_info=True)

        # Set default values in case of error
        context.cooldown_info = {
            "in_cooldown": False,
            "remaining_seconds": 0,
            "cooldown_minutes": 0,
        }

    # Always continue processing to let handler make the final decision
    return True
```

## Command Parsers

### Ticket Parser

```python
from typing import Optional, Tuple
from dataclasses import dataclass

@dataclass
class TicketArgs:
    """Arguments for support ticket commands"""

    action: str  # "open", "close", "list"
    ticket_id: Optional[int] = None
    filter_status: Optional[str] = None  # "all", "open", "closed"
    limit: int = 10  # Default number of tickets to list

    # Allowed values and aliases
    VALID_ACTIONS = ["open", "close", "list"]
    ACTION_ALIASES = {
        "o": "open",
        "reopen": "open",
        "c": "close",
        "l": "list",
        "view": "list",
        "show": "list",
        "get": "list",
    }

    # Filters for listing tickets
    VALID_FILTERS = ["all", "open", "closed"]
    FILTER_ALIASES = {
        "a": "all",
        "o": "open",
        "c": "closed",
    }

def parse_ticket_command(args: list[str]) -> Tuple[Optional[TicketArgs], Optional[str]]:
    """
    Parse arguments for ticket commands

    Handles formats:
    - /ticket open <id>     # Reopen a closed ticket
    - /ticket close <id>    # Close an open ticket
    - /ticket list [all|open|closed] [limit]  # List tickets

    Returns:
        Tuple of (TicketArgs, error_message)
    """
    if not args:
        return None, "Help text for ticket commands..."

    # Get action from first arg
    action = args[0].lower()

    # Check for aliases
    if action in TicketArgs.ACTION_ALIASES:
        action = TicketArgs.ACTION_ALIASES[action]

    # Validate action
    if action not in TicketArgs.VALID_ACTIONS:
        return None, f"Unknown action: {action}. Valid actions are: open, close, list"

    # Create result with normalized action
    result = TicketArgs(action=action)

    # Process based on action type
    if action in ["open", "close"]:
        if len(args) < 2:
            return None, f"Please provide a ticket ID. Example: /ticket {action} 123"

        if not args[1].isdigit():
            return None, f"Invalid ticket ID: {args[1]}. Must be a number."

        result.ticket_id = int(args[1])

    elif action == "list":
        # Default values
        result.filter_status = "all"
        result.limit = 10

        # Check for optional filter
        if len(args) > 1:
            filter_status = args[1].lower()

            # Check for aliases
            if filter_status in TicketArgs.FILTER_ALIASES:
                filter_status = TicketArgs.FILTER_ALIASES[filter_status]

            if filter_status in TicketArgs.VALID_FILTERS:
                result.filter_status = filter_status
            elif filter_status.isdigit():
                # If the second arg is a number, treat it as limit
                result.limit = min(int(filter_status), 50)  # Limit to 50 max
            else:
                return None, f"Invalid filter: {filter_status}. Valid filters are: all, open, closed"

        # Check for optional limit (third argument)
        if len(args) > 2 and args[2].isdigit():
            result.limit = min(int(args[2]), 50)  # Limit to 50 max

    return result, None
```

## Client Registration

Update the TelegramClient class to include the support handlers:

```python
# In client.py __init__ method
self.support_handlers = SupportHandlers(services, settings)

# Add to command_handlers list
self.command_handlers: List[Tuple[Union[str, List[str]], callable]] = [
    # Existing commands...

    # Support Commands
    ("report", self.support_handlers.handle_report),
    ("tickets", self.support_handlers.handle_tickets),
    ("close_ticket", self.support_handlers.handle_close_ticket),
]
```

## Configuration Updates

Add the support ticket settings to the Settings class:

```python
# In shared/config.py
class Settings(BaseSettings):
    # Existing settings...

    # Support ticket settings
    support_channel_id: str = os.getenv("SUPPORT_CHANNEL_ID", "@your_channel")
    report_cooldown_seconds: int = int(os.getenv("REPORT_COOLDOWN_SECONDS", "3600"))  # 1 hour
```

## Migration Options

### Option 1: Alembic Migration Script

```python
"""Create support ticket tables

Revision ID: 20240515001
Revises: 2023071500
Create Date: 2024-05-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = '20240515001'
down_revision = '2023071500'  # Adjust to point to the latest existing migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create support_tickets table
    op.create_table(
        'support_tickets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(100), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default=sa.text("'open'")),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_support_tickets'))
    )

    # Create report_cooldowns table
    op.create_table(
        'report_cooldowns',
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('last_reported_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('user_id', name=op.f('pk_report_cooldowns'))
    )

    # Create indexes
    op.create_index(op.f('ix_support_tickets_user_id'), 'support_tickets', ['user_id'], unique=False)
    op.create_index(op.f('ix_support_tickets_status'), 'support_tickets', ['status'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_support_tickets_status'), table_name='support_tickets')
    op.drop_index(op.f('ix_support_tickets_user_id'), table_name='support_tickets')

    # Drop tables
    op.drop_table('report_cooldowns')
    op.drop_table('support_tickets')
```

### Option 2: Direct SQL Script

```python
#!/usr/bin/env python
"""
Script to create the support ticket tables directly in the Neon PostgreSQL database.
This can be used when Alembic migrations have issues.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parents[1]))

import psycopg
from db.config import DatabaseSettings

CREATE_SUPPORT_TABLES_SQL = """
-- Create support_tickets table
CREATE TABLE IF NOT EXISTS support_tickets (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP,
    user_id BIGINT NOT NULL,
    username VARCHAR(100),
    message TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'open'
);

-- Create report_cooldowns table
CREATE TABLE IF NOT EXISTS report_cooldowns (
    user_id BIGINT PRIMARY KEY,
    last_reported_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS ix_support_tickets_user_id ON support_tickets (user_id);
CREATE INDEX IF NOT EXISTS ix_support_tickets_status ON support_tickets (status);

-- Create a function to update the updated_at field
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

-- Create a trigger to automatically update updated_at
DROP TRIGGER IF EXISTS update_support_tickets_modtime ON support_tickets;
CREATE TRIGGER update_support_tickets_modtime
BEFORE UPDATE ON support_tickets
FOR EACH ROW
EXECUTE FUNCTION update_modified_column();
"""

def create_support_tables():
    """Create the support ticket tables directly in the database."""
    settings = DatabaseSettings()

    # Get connection info from settings
    conn_str = f"host={settings.POSTGRES_HOST} port={settings.POSTGRES_PORT} dbname={settings.POSTGRES_DB} user={settings.POSTGRES_USER} password={settings.POSTGRES_PASSWORD} sslmode=require"

    # Connect to the database
    print(f"Connecting to {settings.POSTGRES_HOST}...")

    try:
        # Connect to the database using synchronous connection
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                # Execute the SQL
                print("Creating support ticket tables...")
                cur.execute(CREATE_SUPPORT_TABLES_SQL)
                conn.commit()
                print("Support ticket tables created successfully!")

                # Verify tables were created
                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'support_tickets')")
                if cur.fetchone()[0]:
                    print("Verified: support_tickets table exists!")
                else:
                    print("Error: support_tickets table was not created!")

                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'report_cooldowns')")
                if cur.fetchone()[0]:
                    print("Verified: report_cooldowns table exists!")
                else:
                    print("Error: report_cooldowns table was not created!")

    except Exception as e:
        print(f"Error creating support ticket tables: {e}")
        return False

    return True

if __name__ == "__main__":
    # Run the function
    success = create_support_tables()
    if success:
        print("Script completed successfully!")
    else:
        print("Script failed!")
        exit(1)
```

## Admin Commands Help Text

Add these entries to the help command responses:

```python
# In handlers/help_handlers.py
help_text += "\n\n**Support Commands**:\n"
help_text += "/report <message> - Submit a support ticket\n"
help_text += "/tickets [limit] - (Admin) List recent support tickets\n"
help_text += "/close_ticket <id> - (Admin) Mark a ticket as closed\n"
```

## Integration Testing Plan

1. **Test Suite**: Create a test suite for the support ticket system
2. **Test Cases**:

   - Submit report with valid message → success
   - Submit report with empty message → error message
   - Submit report with excessively long message → truncated
   - Submit second report within cooldown period → error with time remaining
   - Admin lists tickets → shows proper formatting
   - Admin closes ticket → status updates in database
   - Non-admin attempts admin commands → access denied

3. **Mocking**:
   - Mock database calls for unit testing
   - Mock Telegram API for integration testing
