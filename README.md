# VRChat Bot

VRChatに対話型 AIシステムを実装するためのリポジトリです。


# インストール
## 環境  
- Windows 10 64bit
- Python 3.9  
- Miniforge
- NVIDIA GeForce RTX Graphics card

## コマンド

依存関係をインストールします。
```sh
pip3 install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu117

pip install git+https://github.com/openai/whisper.git@main
```

このリポジトリをクローンし、プロジェクトのルートフォルダで次のコマンドを実行してください。

```sh
pip install .
```

# 使い方  

## OpenAIのAPI KEY 取得
[OpenAIのAPIKEYをここから取得してください](https://beta.openai.com/account/api-keys)  
取得したAPI KEYは `data/API_KEY.txt` に書き込んでください。  


## オーディオデバイスの確認  
次のコマンドを実行して、利用するスピーカとマイクを探します。    

```sh
python -m vrchatbot audio-devices
```

* output  
```
--- Microphones ---
Index: 0, Name: スピーカー (Display Audio)
Index: 1, Name: ヘッドホン (Oculus Virtual Audio Device)

--- Speakers ---
Index: 0, Name: スピーカー (Display Audio)
Index: 1, Name: ヘッドホン (Oculus Virtual Audio Device)
```

使用するマイクとスピーカの名前を`botconfig.toml`の中の `mic_index_or_name`および`speaker_index_or_name`にしてしてください。Indexによる指定も可能ですが、よくその値は変更されるため名前による指定が望ましいです。  

## 実行  
それでは実行してみましょう!  
```sh
python -m vrchatbot run
```

* output   
```
Setting up...
Ready.
Recongnized: <話した声>

Responce: <AIのレスポンス>

...
```

# 仕様詳細  
整備中(もうちょっと待ってね！)  
