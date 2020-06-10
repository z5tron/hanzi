## texlive

texlive-base
texlive-xetex
texlive-lang-chinese

## docker

docker commit container-ID image-name

~~~json
{
  "max-concurrent-uploads" : 2
}
~~~

## PostgreSQL

### Ubuntu 18.04 LTS

- postgresql-server-dev-10 postgresql-server-dev-all
- sudo apt install postgresql postgresql-contrib
- sudo -i -u postgres
- sudo -u postgres psql
- sudo -u postgres createuser --interactive

psql=# create database <dbname>;
psql=# alter user <username> with encrypted password '<password>';
psql=# grant all privileges on database <dbname> to <username> ;

## MySQL

- `sudo apt install mysql-server libmysql-dev`
- `pip install -r requirement.txt`
- `cd; mysqldump -u z5tron -h z5tron.mysql.pythonanywhere-services.com 'z5tron$hanzi'  > db-hanzi-backup-2020-0609.sql`


## Testing

export FLASK_APP=qiangzhi.py
export FLASK_DEBUG=1
export FLASK_CONFIG=production
export FLASK_ENV=development
