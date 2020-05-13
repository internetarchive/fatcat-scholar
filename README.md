
**fatcat-scholar**: fulltext search over [fatcat](https://fatcat.wiki) corpus
of 25+ million open research papers

## Translations

Update the .pot file and translation files:

    pybabel extract -F extra/i18n/babel.cfg -o extra/i18n/web_interface.pot fatcat_scholar/
    pybabel update -i extra/i18n/web_interface.pot -d fatcat_scholar/translations

Compile translated messages together:

    pybabel compile -d fatcat_scholar/translations

Create initial .po file for a new language translation (then run the above
update/compile after doing initial translations):

    pybabel init -i extra/i18n/web_interface.pot -d fatcat_scholar/translations -l de

## Production

Use gunicorn plus uvicorn, to get multiple worker processes, each running
async:

    gunicorn example:app -w 4 -k uvicorn.workers.UvicornWorker
