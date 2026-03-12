# Database Migrations Guide

## Overview

Database migrations are version-controlled SQL scripts that define schema changes. We use **Alembic** to manage migrations.

## What are Migrations?

Migrations allow you to:

- Track database schema changes over time
- Revert to previous versions if needed
- Deploy consistent schema across environments
- Document database evolution

## Migration Workflow

```
Code Changes → Create Migration → Apply Migration → Commit
```

## Creating a Migration

### Automatic Migration (Recommended)

When you modify SQLAlchemy models, Alembic can auto-generate the migration:

```bash
# Create migration (auto-detects model changes)
docker-compose exec api alembic revision --autogenerate -m "Add user verification field"

# This creates: alembic/versions/001_add_user_verification_field_py
```

### Manual Migration

For complex changes that auto-detect can't handle:

```bash
# Create empty migration
docker-compose exec api alembic revision -m "Custom data migration"

# Edit the created file manually in alembic/versions/
```

## Migration File Structure

```python
# alembic/versions/001_add_email_to_users.py
"""Add email to users

Revision ID: 001
Revises: None
Create Date: 2024-03-18

"""
from alembic import op
import sqlalchemy as sa

# This is the unique identifier of the migration
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Run migration forward"""
    op.add_column('users', sa.Column('email', sa.String(255), nullable=False))
    op.create_unique_constraint('uq_users_email', 'users', ['email'])

def downgrade():
    """Revert migration"""
    op.drop_constraint('uq_users_email', 'users')
    op.drop_column('users', 'email')
```

## Common Migration Operations

### Add Column

```python
def upgrade():
    op.add_column('exams', sa.Column('difficulty', sa.String(50)))

def downgrade():
    op.drop_column('exams', 'difficulty')
```

### Add Constraint

```python
def upgrade():
    op.create_unique_constraint('uq_exam_title', 'exams', ['title'])

def downgrade():
    op.drop_constraint('uq_exam_title', 'exams')
```

### Add Index

```python
def upgrade():
    op.create_index('ix_exams_created_at', 'exams', ['created_at'])

def downgrade():
    op.drop_index('ix_exams_created_at', 'exams')
```

### Create Table

```python
def upgrade():
    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('tags')
```

### Data Migration

```python
def upgrade():
    # Update existing data
    connection = op.get_bind()
    connection.execute(
        "UPDATE exams SET difficulty='medium' WHERE difficulty IS NULL"
    )

def downgrade():
    connection = op.get_bind()
    connection.execute(
        "UPDATE exams SET difficulty=NULL WHERE difficulty='medium'"
    )
```

## Applying Migrations

### Apply All Pending Migrations

```bash
# Run all migrations up to current version
docker-compose exec api alembic upgrade head
```

### Apply Specific Number of Migrations

```bash
# Apply next 2 migrations
docker-compose exec api alembic upgrade +2

# Apply to specific revision
docker-compose exec api alembic upgrade 001
```

### Revert Migrations

```bash
# Revert one migration
docker-compose exec api alembic downgrade -1

# Revert to specific revision
docker-compose exec api alembic downgrade 000

# Revert all migrations (careful!)
docker-compose exec api alembic downgrade base
```

## Checking Migration Status

### View Current Revision

```bash
docker-compose exec api alembic current
# Output: 005

docker-compose exec api alembic current -v
# With details about the migration
```

### View Migration History

```bash
docker-compose exec api alembic history
# Output:
# <base> -> 001_initial_schema, empty message
# 001_initial_schema -> 002_add_users, Add users table
# 002_add_users -> 003_add_exams, Add exams table
```

### View Branches

```bash
docker-compose exec api alembic branches
```

## Best Practices

### Migration Naming

```
✅ Add_user_email_field
✅ Create_exams_table
✅ Add_unique_constraint_on_title
❌ update_db
❌ migration_v1
```

## Step-by-Step Example: Add a Field

### 1. Modify Your Model

```python
# app/models/exam.py
from sqlalchemy import Column, String, Integer
from app.database import Base

class Exam(Base):
    __tablename__ = "exams"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    # New field
    difficulty_level = Column(String, default="medium")
```

### 2. Create Migration

```bash
docker-compose exec api alembic revision --autogenerate -m "Add difficulty_level to exams"

# This creates: alembic/versions/003_add_difficulty_level_to_exams.py
```

### 3. Review Generated Migration

```bash
nano alembic/versions/003_add_difficulty_level_to_exams.py
```

Expected content:

```python
def upgrade():
    op.add_column('exams', sa.Column('difficulty_level', sa.String(), nullable=True))

def downgrade():
    op.drop_column('exams', 'difficulty_level')
```

Modify if needed (e.g., set a default value).

### 4. Test Migration Locally

```bash
# Test upgrade
docker-compose exec api alembic upgrade head

# Verify the column was added
docker-compose exec db psql -U examgenie_user -d examgenie -c "\d exams"

# Test downgrade
docker-compose exec api alembic downgrade -1

# Verify column was removed
docker-compose exec db psql -U examgenie_user -d examgenie -c "\d exams"

# Re-apply upgrade for actual use
docker-compose exec api alembic upgrade head
```

### 5. Update Pydantic Schema

```python
# app/schemas/models.py
from pydantic import BaseModel

class ExamCreate(BaseModel):
    title: str
    difficulty_level: str = "medium"

class ExamResponse(BaseModel):
    id: int
    title: str
    difficulty_level: str
```

### 6. Update API Endpoints

```python
# app/routes/exams.py
from app.schemas.models import ExamCreate, ExamResponse

@router.post("/exams", response_model=ExamResponse)
async def create_exam(exam: ExamCreate, db: Session = Depends(get_db)):
    db_exam = Exam(**exam.dict())
    db.add(db_exam)
    db.commit()
    db.refresh(db_exam)
    return db_exam
```

### 7. Commit Changes

```bash
git add alembic/versions/003_add_difficulty_level_to_exams.py
git add app/models/exam.py
git add app/schemas/models.py
git add app/routes/exams.py
git commit -m "feat: add difficulty_level to exams"
```

## Migration in Production

### Deployment Strategy

1. **Build and test** locally
2. **Run migrations** on staging environment first
3. **Monitor** execution time and verify success
4. **Deploy** to production
5. **Run migrations** in production

```bash
# Production
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head
```

### Zero-Downtime Migrations

For production without downtime:

1. **Add column** (nullable)
2. **Deploy code** that reads new column
3. **Backfill data** (while app is handling new writes)
4. **Add constraints** (NOT NULL, unique, etc)

```python
# Step 1: Add nullable column
def upgrade():
    op.add_column('users', sa.Column('email', sa.String(255), nullable=True))

# Step 2-3: App handles NULL emails
# Step 4: Now make it NOT NULL
def upgrade_part2():
    op.alter_column('users', 'email', nullable=False)
```

## Troubleshooting Migrations

### Migration Won't Apply

```bash
# Check current state
docker-compose exec api alembic current

# Check for errors
docker-compose exec api alembic upgrade head --sql  # Preview SQL

# Manual check
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT * FROM alembic_version;"
```

### Rollback Failed

```bash
# If stuck on wrong version, manually update
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "UPDATE alembic_version SET version_num='002';"

# Then retry
docker-compose exec api alembic upgrade head
```

### Conflicting Migrations

```bash
# If multiple migrations created simultaneously
# Manually edit down_revision in newer migration:
# down_revision = '003'  # Points to correct previous migration
```

## Migration Naming Convention

```
000_initial_schema.py
001_create_users_table.py
002_create_exams_table.py
003_add_difficulty_level_to_exams.py
004_create_exam_questions_junction.py
005_add_index_on_exam_id.py
```

## Useful Commands

```bash
# Show all migrations
docker-compose exec api alembic history -v

# Show current version
docker-compose exec api alembic current

# Upgrade to next version
docker-compose exec api alembic upgrade +1

# Downgrade one step
docker-compose exec api alembic downgrade -1

# Show SQL without running (dry run)
docker-compose exec api alembic upgrade head --sql

# Show merge conflicts
docker-compose exec api alembic merge heads

# Drop all (BE CAREFUL!)
docker-compose exec api alembic downgrade base
```

## Related Topics

- See [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md) for database changes workflow
- See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for production migration strategy
