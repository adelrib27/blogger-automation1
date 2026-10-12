# Radar Tech BR — infraestrutura WordPress

Infraestrutura isolada para o primeiro WordPress self-hosted da rede de blogs.

## Objetivo

Subir `radartechbr.com.br` em uma VM OCI Always Free sem alterar o pipeline Blogger existente. O site nasce com publicação automática desativada e preparado para futura integração com a API da Shopee.

## Base recomendada

- Oracle Cloud Infrastructure Always Free
- Ubuntu 24.04 LTS ARM64 em VM.Standard.A1.Flex
- Nginx
- PHP-FPM (versão padrão do Ubuntu 24.04)
- MariaDB
- WP-CLI
- Certbot / Let's Encrypt
- UFW + Fail2ban

## Segurança

Nunca versionar senhas, tokens, chaves privadas, Application Passwords do WordPress ou credenciais da Shopee. Use variáveis de ambiente e GitHub Secrets quando a automação for habilitada.

## Etapa 1 — servidor

```bash
sudo bash bootstrap-server.sh
```

## Etapa 2 — WordPress

Defina as variáveis apenas na sessão atual do terminal e execute o provisionamento:

```bash
export SITE_DOMAIN='radartechbr.com.br'
export DB_NAME='radartechbr_wp'
export DB_USER='radartechbr_wp'
export DB_PASSWORD='gere-uma-senha-forte-aqui'
export WP_TITLE='Radar Tech BR'
export WP_ADMIN_USER='defina-um-usuario-admin-nao-obvio'
export WP_ADMIN_PASSWORD='gere-outra-senha-forte-aqui'
export WP_ADMIN_EMAIL='seu-email-administrativo'

sudo -E bash provision-wordpress.sh
```

Não compartilhe essas variáveis em chats ou commits.

## Etapa 3 — DNS e HTTPS

Somente depois de validar o servidor por IP, aponte o domínio no Registro.br. Após a propagação:

```bash
sudo certbot --nginx -d radartechbr.com.br -d www.radartechbr.com.br --redirect
sudo wp option update home 'https://radartechbr.com.br' --path='/var/www/radartechbr.com.br' --allow-root
sudo wp option update siteurl 'https://radartechbr.com.br' --path='/var/www/radartechbr.com.br' --allow-root
```

## Regras do projeto

1. Blogger continua independente e em produção.
2. Radar Tech BR começa com publicação automática desligada.
3. Tema e automação WordPress permanecem separados.
4. A integração Shopee só será ativada após validar os endpoints realmente liberados para a conta.
5. Cada futuro blog terá credenciais, histórico e anti-duplicação próprios.
