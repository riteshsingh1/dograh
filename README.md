```
bash scripts/deploy_production_docker.sh \
  --domain app.callorax.com \
  --api-domain api.callorax.com \
  --backend-endpoint https://api.callorax.com \
  --configure-nginx \
  --enable-https \
  --certbot-email 1124ritesh@gmail.com \
  --include-coturn
