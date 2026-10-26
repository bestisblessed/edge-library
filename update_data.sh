#!/bin/bash
set -e

rm -rf data
mkdir data
cp -r ~/Code/nfl-ai/Scrapers/data/* data/
cp -r ~/Code/nfl-ai/Scrapers/final_data_pfr data/
rm -f data/Archive.zip

read -r -p "Commit and push refreshed data to main? [y/N] " answer
case "$answer" in
    y|Y)
        if [ "$(git branch --show-current)" != "main" ]; then
            echo "Not on main; refreshed data was not committed or pushed."
            exit 1
        fi

        git add -A data/
        if ! git diff --cached --quiet -- data/; then
            git commit -m "Refresh NFL data" -- data/
            git push origin main
        else
            echo "No data changes to commit."
        fi
        ;;
    *)
        echo "Refreshed data locally; no commit or push."
        ;;
esac
