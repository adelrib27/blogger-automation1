#!/usr/bin/env bash
set -Eeuo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "Execute como root: sudo bash $0" >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get upgrade -y
apt-get install -y \
  nginx mariadb-server \
  php-fpm php-mysql php-curl php-gd php-intl php-mbstring php-soap php-xml php-zip php-imagick \
  unzip curl ca-certificates gnupg jq rsync \
  certbot python3-certbot-nginx \
  fail2ban ufw

systemctl enable --now nginx mariadb fail2ban

ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

mariadb <<'SQL'
DELETE FROM mysql.user WHERE User='';
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';
FLUSH PRIVILEGES;
SQL

if ! command -v wp >/dev/null 2>&1; then
  curl -fsSLo /usr/local/bin/wp https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar
  chmod +x /usr/local/bin/wp
fi

PHP_VERSION="$(php -r 'echo PHP_MAJOR_VERSION.".".PHP_MINOR_VERSION;')"
PHP_INI="/etc/php/${PHP_VERSION}/fpm/php.ini"
if [[ -f "$PHP_INI" ]]; then
  sed -ri 's/^upload_max_filesize\s*=.*/upload_max_filesize = 64M/' "$PHP_INI"
  sed -ri 's/^post_max_size\s*=.*/post_max_size = 64M/' "$PHP_INI"
  sed -ri 's/^memory_limit\s*=.*/memory_limit = 256M/' "$PHP_INI"
  sed -ri 's/^max_execution_time\s*=.*/max_execution_time = 120/' "$PHP_INI"
fi
systemctl restart "php${PHP_VERSION}-fpm"

echo "=== Radar Tech BR server base ready ==="
echo "Nginx: $(nginx -v 2>&1)"
echo "PHP: $(php -r 'echo PHP_VERSION;')"
echo "MariaDB: $(mariadb --version)"
echo "WP-CLI: $(wp --info --allow-root | head -n 1)"
echo "UFW: $(ufw status | head -n 1)"
