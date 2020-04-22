python extraction.py "$@" > tmp.sql
psql stocks -f tmp.sql
