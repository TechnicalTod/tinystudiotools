# Support Ticket System - PRD

## Overview

The Support Ticket System enables users to submit reports or issues directly to the development team through the bot. This feature provides a structured way for users to communicate problems, request features, or ask for help, while maintaining control through cooldown periods to prevent spam.

## Purpose

- **User Feedback**: Allow users to easily report issues or provide feedback
- **Centralized Monitoring**: Channel all support requests to a dedicated development channel
- **Abuse Prevention**: Implement cooldown periods to prevent spam
- **Administration**: Provide tools for admins to manage and respond to tickets

## User Stories

### User Stories

1. As a user, I want to report issues I encounter with the bot
2. As a user, I want confirmation that my report was received
3. As a user, I want to know if I need to wait before submitting another report
4. As a user, I want clear instructions on how to format my report

### Admin Stories

1. As an admin, I want to see all submitted tickets in a central location
2. As an admin, I want to mark tickets as closed when resolved
3. As an admin, I want to limit how frequently a user can submit reports
4. As an admin, I want to see basic information about the user who submitted a ticket and be able to message them

## Functional Requirements

### Core Functionality

- Accept user reports via the `/report` command
- Store reports in a PostgreSQL database with appropriate metadata
- Enforce per-user cooldown periods (e.g., one report per hour)
- Forward reports to a dedicated Telegram channel for admin review
- Track ticket status (open/closed)

### User Commands

- `/report [message]` - Submit a new support ticket with the message content

### Admin Commands

- `/tickets [limit]` - List recent open support tickets (default 10, max 50)
- `/close_ticket [id]` - Mark a ticket as closed
- `/ticket [action] [options]` - Unified ticket management:
  - `/ticket open <id>` - Reopen a closed ticket
  - `/ticket close <id>` - Close an open ticket
  - `/ticket list [filter] [limit]` - List tickets with filter (all/open/closed)

### Cooldown System

- Track timestamp of last report for each user
- Enforce configurable cooldown period (default: 1 hour)
- Provide remaining cooldown time in rejection messages

## Technical Requirements

### Database Structure

#### Support Tickets Table

- `id`: Primary key
- `user_id`: Telegram user ID (BigInteger)
- `username`: Telegram username (if available)
- `message`: The content of the report
- `created_at`: Timestamp when the ticket was created
- `status`: Current status (open/closed)

#### Report Cooldowns Table

- `user_id`: Telegram user ID (BigInteger, primary key)
- `last_reported_at`: Timestamp of the user's most recent report

### Implementation Details

- Middleware for cooldown management
- Handler for ticket creation and admin commands
- Database repositories for persistent storage
- Clean input validation and sanitization
- Environmental variables for configuration

## Out of Scope

- Complex ticketing workflows (assignment, priorities, etc.)
- Direct admin-to-user communication through the bot
- Ticket categories or tags
- Attachments (images, files)

## Future Considerations

- Ticket categories (bug, feature request, etc.)
- Ability to attach screenshots or files to reports
- Admin assignment of tickets to specific developers
- User notification when ticket status changes
- Integration with external ticketing systems

## Success Metrics

- Users can successfully submit reports
- Cooldown system effectively prevents spam
- Admins can view and manage tickets
- Development team receives timely notifications of new issues
