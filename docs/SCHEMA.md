# Database Schema

SQLite database stored at `/app/data/kanban.db` (mounted as a Docker volume).

## Tables

### users

| Column   | Type    | Constraints              |
|----------|---------|--------------------------|
| id       | INTEGER | PRIMARY KEY AUTOINCREMENT|
| username | TEXT    | NOT NULL UNIQUE          |

Single row for the MVP ("user"). Exists so the schema is ready for multi-user later.

### boards

| Column  | Type    | Constraints                          |
|---------|---------|--------------------------------------|
| id      | INTEGER | PRIMARY KEY AUTOINCREMENT            |
| user_id | INTEGER | NOT NULL REFERENCES users(id) UNIQUE |
| title   | TEXT    | NOT NULL DEFAULT 'My Board'          |

One board per user for the MVP. The UNIQUE on user_id enforces this.

### columns

| Column   | Type    | Constraints                       |
|----------|---------|-----------------------------------|
| id       | INTEGER | PRIMARY KEY AUTOINCREMENT         |
| board_id | INTEGER | NOT NULL REFERENCES boards(id)    |
| title    | TEXT    | NOT NULL                          |
| position | INTEGER | NOT NULL                          |

Position is 0-indexed and determines left-to-right ordering. Five default columns are seeded.

### cards

| Column    | Type    | Constraints                        |
|-----------|---------|------------------------------------|
| id        | INTEGER | PRIMARY KEY AUTOINCREMENT          |
| column_id | INTEGER | NOT NULL REFERENCES columns(id)    |
| title     | TEXT    | NOT NULL                           |
| details   | TEXT    | NOT NULL DEFAULT ''                |
| position  | INTEGER | NOT NULL                           |

Position is 0-indexed within a column and determines top-to-bottom ordering.

## Seed data

On first login, a user gets a board with five columns (Backlog, Discovery, In Progress, Review, Done) and the eight sample cards matching the current frontend demo.

## Notes

- All IDs are auto-incrementing integers (not the string IDs currently used in frontend state). The frontend will adapt.
- Cascade deletes are not used; the app manages deletion order explicitly.
- No timestamps for MVP; can be added later.
