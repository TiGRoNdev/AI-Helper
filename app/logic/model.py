# SPDX-License-Identifier: LGPL-2.1-or-later


import json
import logging
import os
import re
import aiohttp


async def get_title_from_message(message):
    async with aiohttp.ClientSession() as session:
        url = f"https://{os.environ['MODEL_HOST']}/api/chat"
        data = {
            "model": os.environ['MODEL_THINK_NAME'],
            "messages": [
                {
                    "role": "user",
                    "content": f"Make a title out of this text no more than 30 characters: "
                               f"'{message}'\n[Provide only answer without additional information]"
                }
            ],
            "stream": False
        }

        async with session.post(url, json=data) as response:
            if response.status == 200:
                answer = await response.json()
                answer = answer['message']['content']
            else:
                logging.warning("Can't make a title out of the text")
                answer = "Title"

        return re.sub(r"<think>(.*)</think>", " ", answer, flags=re.DOTALL).strip()


async def streaming_response_generator(messages):
    async with aiohttp.ClientSession() as session:
        url = f"https://{os.environ['MODEL_HOST']}/api/chat"
        data = {
            "model": os.environ['MODEL_THINK_NAME'],
            "messages": messages
        }

        async with session.post(url, json=data) as response:
            async for data, _ in response.content.iter_chunks():
                resp = json.loads(data.decode("utf-8"))
                yield resp["message"]["content"]

