#!/usr/bin/env bash
set -Eeuo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "Execute como root: sudo bash $0" >&2
  exit 1
fi

required=(SITE_DOMAIN DB_NAME DB_USER DB_PASSWORD WP_ADMIN_USER WP_ADMIN_PASSWORD WP_ADMIN_EMAIL WP_TITLE)
for var in "${required[@]}"; do
  if [[ -z "${!var:-}" ]]; then
    echo "Variável obrigatória ausente: $var" >&2
    exit 1
  fi
done

SITE_ROOT="/var/www/${SITE_DOMAIN}"
PHP_VERSION="$(php -r 'echo PHP_MAJOR_VERSION.".".PHP_MINOR_VERSION;')"
PHP_SOCK="/run/php/php${PHP_VERSION}-fpm.sock"

mariadb <<SQL
CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD//\'/\'\'}';
ALTER USER '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD//\'/\'\'}';
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'localhost';
FLUSH PRIVILEGES;
SQL

mkdir -p "$SITE_ROOT"
if [[ ! -f "$SITE_ROOT/wp-load.php" ]]; then
  wp core download --path="$SITE_ROOT" --locale=pt_BR --allow-root
fi

if [[ ! -f "$SITE_ROOT/wp-config.php" ]]; then
  wp config create \
    --path="$SITE_ROOT" \
    --dbname="$DB_NAME" \
    --dbuser="$DB_USER" \
    --dbpass="$DB_PASSWORD" \
    --dbhost=localhost \
    --dbprefix=wp_ \
    --skip-check \
    --allow-root
fi

wp config set DISALLOW_FILE_EDIT true --raw --path="$SITE_ROOT" --allow-root
wp config set WP_AUTO_UPDATE_CORE minor --path="$SITE_ROOT" --allow-root
wp config set WP_MEMORY_LIMIT 256M --path="$SITE_ROOT" --allow-root

if ! wp core is-installed --path="$SITE_ROOT" --allow-root >/dev/null 2>&1; then
  wp core install \
    --path="$SITE_ROOT" \
    --url="http://${SITE_DOMAIN}" \
    --title="$WP_TITLE" \
    --admin_user="$WP_ADMIN_USER" \
    --admin_password="$WP_ADMIN_PASSWORD" \
    --admin_email="$WP_ADMIN_EMAIL" \
    --skip-email \
    --allow-root
fi

chown -R www-data:www-data "$SITE_ROOT"
find "$SITE_ROOT" -type d -exec chmod 755 {} \;
find "$SITE_ROOT" -type f -exec chmod 644 {} \;

cat > "/etc/nginx/sites-available/${SITE_DOMAIN}" <<NGINX
server {
    listen 80;
    listen [::]:80;
    server_name ${SITE_DOMAIN} www.${SITE_DOMAIN};

    root ${SITE_ROOT};
    index index.php index.html;

    client_max_body_size 64M;

    location / {
        try_files \$uri \$uri/ /index.php?\$args;
    }

    location ~ \.php$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:${PHP_SOCK};
    }

    location ~* /(?:uploads|files)/.*\.php$ {
        deny all;
    }

    location ~ /\.ht {
        deny all;
    }
}
NGINX

ln -sfn "/etc/nginx/sites-available/${SITE_DOMAIN}" "/etc/nginx/sites-enabled/${SITE_DOMAIN}"
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

wp rewrite structure '/%postname%/' --path="$SITE_ROOT" --allow-root
wp option update timezone_string 'America/Recife' --path="$SITE_ROOT" --allow-root
wp option update blogdescription 'Tecnologia, eletrônicos, smart home, gadgets e ferramentas.' --path="$SITE_ROOT" --allow-root
wp option update default_comment_status closed --path="$SITE_ROOT" --allow-root
wp option update default_ping_status closed --path="$SITE_ROOT" --allow-root

cat <<MSG
WordPress provisionado em HTTP.
Próximo passo: aponte DNS de ${SITE_DOMAIN} e www.${SITE_DOMAIN} para este servidor.
Depois rode:
  sudo certbot --nginx -d ${SITE_DOMAIN} -d www.${SITE_DOMAIN} --redirect
Em seguida ajuste as URLs para HTTPS:
  sudo wp option update home 'https://${SITE_DOMAIN}' --path='${SITE_ROOT}' --allow-root
  sudo wp option update siteurl 'https://${SITE_DOMAIN}' --path='${SITE_ROOT}' --allow-root
MSG
