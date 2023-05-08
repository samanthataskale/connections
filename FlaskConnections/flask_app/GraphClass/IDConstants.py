"""Constants for author 'id'ing. Need to know id for an author
has a id or placeholder for each database."""

NUM_DATABASES = 2 # number of databases we are using
DEFAULT_ID = "skip" # the default when not using database

NEED_ID = 0 # don't know id yet
ID_NOT_FOUND = 1 # We tried to look it up but couldn't find it

PUBLICATION = 0 # index of semantic scholar id
PATENT = 1 # index of patent id