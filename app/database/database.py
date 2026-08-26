import asyncpg
import os

pool = None


async def connect():
    global pool

    pool = await asyncpg.create_pool(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        min_size=1,
        max_size=10,
    )

    print("✅ PostgreSQL pool connected")


async def create_ticket(chat_id, chat_title, first_message):
    async with pool.acquire() as conn:
        ticket_id = await conn.fetchval(
            """
            INSERT INTO tickets (
                chat_id,
                chat_title,
                first_message,
                last_activity_at
            )
            VALUES ($1, $2, $3, NOW())
            RETURNING id
            """,
            chat_id,
            chat_title,
            first_message,
        )

    return ticket_id


async def update_first_response(
    ticket_id,
    response_time,
    employee_id
):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE tickets
            SET
                first_response_at = NOW(),
                first_response_seconds = $1,
                first_responder_id = $2,
                sla_completed = TRUE
            WHERE id = $3
            """,
            response_time,
            employee_id,
            ticket_id,
        )


async def update_sla_notification(ticket_id):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE tickets
            SET sla_notified = TRUE
            WHERE id = $1
            """,
            ticket_id,
        )


async def close_ticket(ticket_id):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE tickets
            SET
                status = 'CLOSED',
                closed_at = NOW()
            WHERE id = $1
            """,
            ticket_id,
        )


async def get_open_ticket(chat_id):
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """
            SELECT *
            FROM tickets
            WHERE chat_id = $1
              AND status = 'OPEN'
            ORDER BY id DESC
            LIMIT 1
            """,
            chat_id,
        )


async def update_last_activity(ticket_id):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE tickets
            SET last_activity_at = NOW()
            WHERE id = $1
            """,
            ticket_id,
        )


async def get_inactive_tickets(timeout_minutes):
    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT *
            FROM tickets
            WHERE status = 'OPEN'
              AND last_activity_at <= NOW() - ($1 * INTERVAL '1 minute')
            """,
            timeout_minutes,
        )


async def get_sla_violations(timeout_minutes):
    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT *
            FROM tickets
            WHERE status = 'OPEN'
              AND sla_completed = FALSE
              AND sla_notified = FALSE
              AND opened_at <= NOW() - ($1 * INTERVAL '1 minute')
            """,
            timeout_minutes,
        )


async def has_open_ticket(chat_id):
    async with pool.acquire() as conn:
        return await conn.fetchval(
            """
            SELECT EXISTS(
                SELECT 1
                FROM tickets
                WHERE chat_id = $1
                  AND status = 'OPEN'
            )
            """,
            chat_id,
        )


async def get_first_response_seconds(chat_id):
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """
            SELECT
                id,
                EXTRACT(EPOCH FROM (NOW() - opened_at))::INT AS response_time,
                sla_completed
            FROM tickets
            WHERE chat_id = $1
              AND status = 'OPEN'
            ORDER BY id DESC
            LIMIT 1
            """,
            chat_id,
        )
    
async def get_employee_by_telegram_id(telegram_id):
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """
            SELECT id
            FROM employees
            WHERE telegram_id = $1
              AND is_active = TRUE
            """,
            telegram_id,
        )