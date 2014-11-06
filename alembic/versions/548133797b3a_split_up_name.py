"""Split up name in first- and lastname.

Revision ID: 548133797b3a
Revises: 53cb1afe4fe6
Create Date: 2014-11-06 02:48:44.950664

"""

# revision identifiers, used by Alembic.
revision = '548133797b3a'
down_revision = '53cb1afe4fe6'

from alembic import op
import sqlalchemy as sa

connection = op.get_bind()

contacthelper = sa.Table(
    'contacts',
    sa.MetaData(),
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('name', sa.String(100)),
    sa.Column('firstname', sa.String(30)),
    sa.Column('lastname', sa.String(70)),
)

def upgrade():
    # we add the new columns first
    op.add_column(
        'contacts',
        sa.Column('firstname', sa.String(30), nullable=True),
    )
    op.add_column(
        'contacts',
        sa.Column('lastname', sa.String(70), nullable=True),
    )

    # at this state right now, the old column is not deleted and the new
    # columns are present already. So no is the time to run the content
    # migration. We use the connection to grab all data from the table, split
    # up name into first- and lastname and update the row, which is identified
    # by its id.

    print(">>>", contacthelper.select())

    for contact in connection.execute(contacthelper.select()):
        firstname, lastname = contact.name.split(' ')
        connection.execute(
            contacthelper.update().where(
                contacthelper.c.id==contact.id
            ).values(
                firstname=firstname,
                lastname=lastname
            )
        )

    # now that all data is migrated we can just drop the old column without
    # having lost any data.
    op.drop_column('contacts', 'name')


def downgrade():
    # for downgrading we do it exactly the other way around we add the old
    # column again
    op.add_column(
        'contacts',
        sa.Column('name', sa.String(100), nullable=True),
    )

    # select all data, join first- and lastname together to name and update the
    # entry identified by it's id.

    for contact in connection.execute(contacthelper.select()):
        name = "%s %s" % (contact.firstname, contact.lastname)
        connection.execute(
            contacthelper.update().where(
                contacthelper.c.id==contact.id
            ).values(name=name)
        )

    # now we can drop the two new columns without having lost any data.
    op.drop_column('contacts', 'firstname')
    op.drop_column('contacts', 'lastname')
