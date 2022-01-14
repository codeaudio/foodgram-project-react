# praktikum_new_diplom
автор codeaudio
* документация
  * http://foodgram.hopto.org/api/docs/
* Суперюзер
  * email admin@admin.com
  * pass admin
  
* рзаворачивание проекта
  * создать файл .env в директории backend
    * пример
      * DB_ENGINE=django.db.backends.postgresql
        DB_NAME=postgres
        POSTGRES_USER=postgres
        POSTGRES_PASSWORD=postgres
        DB_HOST=db
        DB_PORT=5432
        SECRET_KEY=secret_key
        HOST=*
        ADMIN_EMAIL=admin.email@example.com
  * локально можно убрать из nginx.conf 
      * listen 443 ssl;
      *  server_tokens off;
      * server_name *.foodgram.hopto.org (заменить на 127.0.0.1); 
      * ssl_certificate /etc/letsencrypt/live/foodgram.hopto.org/fullchain.pem;
      * ssl_certificate_key /etc/letsencrypt/live/foodgram.hopto.org/privkey.pem;      
  * перейти backend/infra/
    * выполнить docker compose up --build