# hanzi
Hanzi

## Heroku

- sudo apt-get install postgresql
- which psql
- sudo -u postgres createuser OWNING_USER
- sudo -u postgres createdb -O OWNING_USER hanzi
- psql hanzi
- sudo apt-get install python3-gunicorn
- heroku create magic-mama-067
- git push heroku master
- heroku ps:scale web=1
- heroku open


~~~json
{
  "max-concurrent-uploads" : 2
}
~~~



