#!/bin/bash

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    . venv/bin/activate
elif [ -d "env" ]; then
    . env/bin/activate
fi

# Run the bot, passing along any arguments
python3 -m tg_bot "$@"
