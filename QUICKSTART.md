# Quick Start - Telegram Bot

## Start the Bot

```bash
# Start all services (bot + MinIO)
docker-compose up -d

# View logs
docker-compose logs -f telegram_bot
```

## Test the Bot

1. Open Telegram
2. Search for your bot (the username you created with @BotFather)
3. Send `/start`
4. Send a test prompt: `a cute cat wearing sunglasses`
5. Wait ~30-60 seconds
6. Receive your generated image!

## Example Prompts

```
a beautiful sunset over mountains, professional photography, 8k
cyberpunk city at night, neon lights, highly detailed
portrait of a cat, professional photography, sharp focus
fantasy dragon, detailed scales, epic, concept art
```

## Commands

- `/start` - Welcome message
- `/help` - Detailed help
- `/settings` - View current settings

## Stop the Bot

```bash
# Stop services
docker-compose down

# Stop and remove volumes (deletes stored images)
docker-compose down -v
```

## View MinIO Console

Access at: http://localhost:9001
- Username: minioadmin
- Password: minioadmin

## Troubleshooting

**Bot not responding?**
```bash
docker-compose logs telegram_bot
docker-compose restart telegram_bot
```

**Check if running:**
```bash
docker-compose ps
```

**Rebuild after changes:**
```bash
docker-compose up -d --build
```
