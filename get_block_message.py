def get_feeling_block(target_user:str):
    blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{target_user}さん、今日の気分を教えてください:relaxed:"
                },
                "accessory": {
                    "type": "radio_buttons",
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": ":one:良好:blush:",
                                "emoji": True
                            },
                            "value": "high"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": ":two:普通:slightly_smiling_face:",
                                "emoji": True
                            },
                            "value": "medium"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": ":three:どよーん:weary:",
                                "emoji": True
                            },
                            "value": "low"
                        }
                    ],
                    "action_id": "radio_buttons-action"
                }
            }
        ]

    return blocks