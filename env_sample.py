def get_env_variable(key):

    env_variable_dict = {
        # ------------------------------------
        # Azure Storage
        # ------------------------------------
        "AZURE_STORAGE_NAME" : "",
        "AZURE_STORAGE_KEY" : "",
        
        # ------------------------------------
        # OpenAI
        # ------------------------------------
        "OPEN_AI_KEY" : "",

        # ------------------------------------
        # App名：Slack_Python_Flask
        # ------------------------------------
        # BotユーザーID
        "BOT_USER_ID" : "",
        # Botトークン（Flask）
        "WEBAPPS_SLACK_TOKEN" : "",
        "WEBAPPS_SIGNING_SECRET" : "",

        # Botトークン（ソケットモード）
        "SOCK_SLACK_BOT_TOKEN" : "",
        "SOCK_SLACK_APP_TOKEN" : ""
    }
    ret_val = env_variable_dict.get(key, None)
    return ret_val


# ------------------------------------
# 環境変数の取得
# ------------------------------------
import os
# 安全な環境変数読み込み関数
def require(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v