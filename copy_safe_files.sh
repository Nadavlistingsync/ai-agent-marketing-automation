#!/bin/bash

echo "🔐 Copying SAFE files for transfer (NO API KEYS)"
echo "================================================"

# Create destination directory
DEST_DIR="../Xeinst_Transfer_Safe"
mkdir -p "$DEST_DIR"

echo "📁 Creating safe copy in: $DEST_DIR"

# Copy safe files only
echo "📋 Copying code files..."

# Main application files
cp moderation_dashboard.py "$DEST_DIR/"
cp moderation_worker.py "$DEST_DIR/"
cp create_sample_data.py "$DEST_DIR/"
cp bluesky_client.py "$DEST_DIR/"
cp requirements_moderation.txt "$DEST_DIR/"
cp env.moderation.example "$DEST_DIR/"

# Templates
mkdir -p "$DEST_DIR/templates"
cp templates/*.html "$DEST_DIR/templates/"

# Reddit bot files
mkdir -p "$DEST_DIR/xeinst_reddit_bot"
cp xeinst_reddit_bot/*.py "$DEST_DIR/xeinst_reddit_bot/"
cp xeinst_reddit_bot/*.yaml "$DEST_DIR/xeinst_reddit_bot/"
cp xeinst_reddit_bot/*.txt "$DEST_DIR/xeinst_reddit_bot/"
cp xeinst_reddit_bot/env.example "$DEST_DIR/xeinst_reddit_bot/"

# Prompts
mkdir -p "$DEST_DIR/xeinst_reddit_bot/prompts"
cp xeinst_reddit_bot/prompts/*.txt "$DEST_DIR/xeinst_reddit_bot/prompts/"

# Documentation
cp README.md "$DEST_DIR/"
cp PROFESSIONAL_SYSTEM.md "$DEST_DIR/"
cp SYSTEM_STATUS_FINAL.md "$DEST_DIR/"
cp SECURE_TRANSFER_GUIDE.md "$DEST_DIR/"
cp .gitignore "$DEST_DIR/"

echo "✅ Safe files copied successfully!"
echo ""
echo "🚫 NOT copied (for security):"
echo "   - .env files (contain API keys)"
echo "   - Database files"
echo "   - Virtual environment"
echo "   - Cache files"
echo "   - Log files"
echo ""
echo "📦 Transfer package ready in: $DEST_DIR"
echo "🔐 Your API keys are safe and not included!"
echo ""
echo "📋 Next steps:"
echo "1. Copy the $DEST_DIR folder to your new computer"
echo "2. Follow SECURE_TRANSFER_GUIDE.md"
echo "3. Add your API keys to new .env files on new computer"
