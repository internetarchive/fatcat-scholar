
## HOWTO: Translations

Update the .pot file and translation files:

    pybabel extract -F extra/i18n/babel.cfg -o extra/i18n/web_interface.pot fatcat_scholar/
    pybabel update -i extra/i18n/web_interface.pot -d fatcat_scholar/translations

Compile translated messages together:

    pybabel compile -d fatcat_scholar/translations

Create initial .po file for a new language translation (then run the above
update/compile after doing initial translations):

    pybabel init -i extra/i18n/web_interface.pot -d fatcat_scholar/translations -l de
