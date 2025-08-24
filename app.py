
import os
from dotenv import load_dotenv
load_dotenv()  # .env を読み込む（ローカル用）
from slack_bolt import App
from slack_sdk import WebClient
# Flaskクラスのインポート
from flask import Flask, request,jsonify
from slack_bolt.adapter.flask import SlackRequestHandler
#ソケットモード用
from slack_bolt.adapter.socket_mode import SocketModeHandler
# ロギング
import traceback
from log_utils import prepare_logger
# Azure Storage（変更点①：新SDKに切替）
from azure.data.tables import TableServiceClient, UpdateMode
from azure.core.credentials import AzureNamedKeyCredential
# Blockの取得
import get_block_message

# モードに応じて書き換え
BOT_USER_ID = os.environ.get("BOT_USER_ID")
# Botトークン（Flask）
WEBAPPS_SLACK_TOKEN = os.environ.get("WEBAPPS_SLACK_TOKEN")
WEBAPPS_SIGNING_SECRET = os.environ.get("WEBAPPS_SIGNING_SECRET")
# Botトークン（ソケットモード）
SOCK_SLACK_BOT_TOKEN = os.environ.get("SOCK_SLACK_BOT_TOKEN")
SOCK_SLACK_APP_TOKEN = os.environ.get("SOCK_SLACK_APP_TOKEN")

# モード入れ替え（WebAPサーバ実行＝Flask／ローカル実行＝ソケットモード)
def app_mode_change(i_name):
    if i_name == "__main__":
        return App(token=SOCK_SLACK_BOT_TOKEN)
    else:
        return App(token=WEBAPPS_SLACK_TOKEN, signing_secret=WEBAPPS_SIGNING_SECRET)

# グローバルオブジェクト
s_app = app_mode_change(__name__)
# Flaskクラスのインスタンス生成
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
handler_flask, handler_socket = None,None

#ソケットーモードの場合のハンドラ設定
if __name__ == "__main__":
    handler_socket = SocketModeHandler(app=s_app, app_token=SOCK_SLACK_APP_TOKEN, trace_enabled=True)
#Flaskでのハンドラー設定
else:
    handler_flask = SlackRequestHandler(s_app)

# Flask httpエンドポイント
# 疎通確認用1
@app.route('/', methods=['GET', 'POST'])
def home():
    return "Hello World Rainbow 2!!"
# 疎通確認用2
@app.route("/test", methods=['GET', 'POST'])
def hello_test():
    return "Hello, This is test.2!!"

# #イベント登録されたリクエストを受け付けるエンドポイント
@app.route("/slack/events", methods=["POST"])
def slack_events():

    # # ------------------------------------
    # # Challenge用
    # # ------------------------------------
    # # Slackから送られてくるPOSTリクエストのBodyの内容を取得
    # # Content-Typeが違っても強制的にJSONとして読み込む
    # json_data = request.get_json(force=True, silent=True)
    # print(json_data)

    # if not json_data or 'challenge' not in json_data:
    #     return "Invalid request", 400

    # # challengeを返却
    # return jsonify({'challenge': json_data['challenge']})

    # ------------------------------------
    # 本番用
    # ------------------------------------
    return handler_flask.handle(request)

# # Interactive操作のリクエストを受け付けるエンドポイント
# @app.route("/slack/interactive", methods=["POST"])
# def slack_interactive():
#     return handler_flask.handle(request)

@s_app.event("message")
@s_app.event("app_mention")
def respondToRequestMsg(body, client:WebClient, ack):
    logger = prepare_logger()
    ack()
    type = body["event"].get("type", None)
    # 二重で応答するのを防ぐため、メンションの時のイベントのみ応答対象とする
    logger.info(f"respondToRequestMsg - イベント種別： {type}")
    if type == 'app_mention':
        try:
            #-----------------------------------
            # Slackのイベント情報から各種パラメータを取得
            input_text = body["event"].get("text", None)
            bot_user_id = os.environ.get('BOT_USER_ID')
            channel = body["event"]["channel"]
            ts = body["event"]["ts"]
            thread_ts = body["event"].get("thread_ts", ts)
            user = body["event"]["user"]
            attachment_files = body["event"].get("files", None)

            # Slackに返答
            # client.chat_postMessage(channel=channel, text=input_text ,thread_ts=ts)
            client.chat_postMessage(channel=channel, blocks=get_block_message.get_feeling_block(user), thread_ts=thread_ts)
            logger.info(f"respondToRequestMsg - Slackへの投稿完了： {input_text}")

            # 投稿内容をDBに保存（変更点②：新SDKでの保存処理）
            storage_name = os.getenv("AZURE_STORAGE_NAME")
            storage_key = os.getenv("AZURE_STORAGE_KEY")
            credential = AzureNamedKeyCredential(storage_name, storage_key)
            service = TableServiceClient(endpoint=f"https://{storage_name}.table.core.windows.net", credential=credential)
            table_client = service.get_table_client("TestTable")
            entity = {
                "PartitionKey":channel,
                "RowKey":ts,
                "ChannelId":channel, 
                "PosterUserDisplayName":user,
                # "PosterUserId":user_id,
                # "PosterUserName":user_name,
            }
            table_client.upsert_entity(entity=entity, mode=UpdateMode.REPLACE)
            logger.info(f"respondToRequestMsg - Azure StorageへのINSERT完了")
        except Exception as e:
            trace = traceback.extract_tb(e.__traceback__)
            error_line = trace[-1].lineno
            logger.info(f"respond_to_message - 例外発生__エラーが発生した行数=： {error_line} エラー内容={str(e)}")

# ehemeralメッセージの削除
@s_app.action("action_react_exec_request_delete")
def delete_first_ephemeral(ack, action, respond):
    ack()
    respond(delete_original=True)

# __name__はPythonにおいて特別な意味を持つ変数です。
# 具体的にはスクリプトの名前を値として保持します。
# この記述により、Flaskがmainモジュールとして実行された時のみ起動する事を保証します。
# （それ以外の、例えば他モジュールから呼ばれた時などは起動しない）
if __name__ == '__main__':
    EXEC_MODE = "SLACK_SOCKET_MODE"
    # Slack ソケットモード実行
    if EXEC_MODE == "SLACK_SOCKET_MODE":
        handler_socket.start()
    # Flask Web/APサーバ 実行
    elif EXEC_MODE == "FLASK_WEB_API":
        # Flaskアプリの起動
        # →Webサーバが起動して、所定のURLからアクセス可能になります。
        # →hostはFlaskが起動するサーバを指定しています（今回はローカル端末）
        # →portは起動するポートを指定しています（デフォルト5000）
        port = int(os.getenv("PORT", 8000))  # 環境変数 PORT を取得し、デフォルト値を 8000 に設定
        app.run(host="0.0.0.0", port=port)  # Azure App Serviceでは host="0.0.0.0" を指定
