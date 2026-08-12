# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

Kaggle コンペ **RSNA Knee Abnormality Detection**（膝 MRI から 12 所見を予測）の作業リポジトリ。
EDA から 2.5D モデリングへ進める過程を、ノートブック単位で積み上げていく構成。

- タスク: 1 study（複数 series の DICOM）に対し 12 ラベル（ACL / MCL / Medial・Lateral Meniscus / Medial・Lateral・PF OA / Effusion / Synovitis / Baker's / Contusion / Fracture）の確率を出力
- 評価: 12 ラベルの ROC AUC の非加重平均（順序のみが効くため、アンサンブルは確率平均ではなく **rank 平均**）
- ドキュメント・コミットメッセージは日本語。コミットは gitmoji プレフィックス（例: `📈 ラベルありデータのみの抽出`）

## コマンド

パッケージ管理は **uv**（Python 3.13）。`.venv/` はコミット対象外。

```bash
uv sync                                            # 依存関係の同期
uv run marimo edit notebooks/00_analysis/count_label_exist.py   # ノートブックを編集モードで開く
uv run marimo run  notebooks/00_analysis/count_label_exist.py   # アプリとして実行
uv run python notebooks/00_analysis/count_label_exist.py        # ヘッドレス実行（marimo は素の .py としても走る）
uv run ruff check .                                # Lint
uv run ruff format .                               # フォーマット
uv run pytest                                      # テスト（現状テストは未整備）
uv run kaggle competitions download -c rsna-knee-abnormality-detection   # データ取得（要 .env の KAGGLE_API_TOKEN）
```

ruff / pytest の設定は `pyproject.toml` に未記述（デフォルト設定で動作）。

## ディレクトリ構造の規約

`notebooks/` と `scripts/` は **番号付きステージ名で対応付ける**。ステージを増やすときは両方に同じ名前のディレクトリを切る。

| ディレクトリ | 用途 |
|---|---|
| `notebooks/00_analysis/` | EDA・集計。marimo ノートブック |
| `notebooks/01_preprocess/`, `scripts/01_preprocess/` | 前処理（未着手、`.gitkeep` のみ） |
| `notebooks/10_reference/` | 他者の公開ノートブック等の参照資料（`.ipynb` のまま置く。編集対象ではない） |
| `notebooks/99_other/` | その他 |
| `scripts/workflows/` | CI 用スクリプト（Node.js） |

### marimo ノートブック

`notebooks/` 配下の自作ノートブックは **`.ipynb` ではなく marimo 形式の `.py`**（`@app.cell` デコレータ）。
セル間のデータ受け渡しは暗黙のグローバルではなく **戻り値のタプル**で行われる（`return (df_has_label,)` → 次セルの引数）。セルを追加・改変したら戻り値と引数の対応も更新すること。

成果物の出力先は `data/artifacts/<ステージ名>/<ノートブック名>/` に揃える（例: `data/artifacts/00_analysis/count_label_exist/`）。`OUTPUT_DIR.mkdir(parents=True, exist_ok=True)` をノートブック冒頭で行う。

## データ

`data/` は **全体が .gitignore 対象**。ローカルにのみ存在する。

```
data/raw_dataset/
├── train.csv          # StudyInstanceUID, Report, + 12 ラベル列
├── train_series.csv   # StudyInstanceUID, SeriesInstanceUID, Fluid_Sensitive, Fat_Suppression, Anatomical_Plane
├── test.csv           # Report 列なし
├── test_series.csv
├── train_series/{StudyInstanceUID}/{SeriesInstanceUID}/*.dcm
└── test_series/ 同上
```

重要な性質:
- **ラベルは疎**。`train.csv` の大半の行は 12 ラベルが null で、`Report`（放射線科レポート）のみを持つ。ラベルあり行の抽出は `df[df['ACL'].notnull()]` が既存の慣行。
- **`Report` は train にのみ存在し test にはない**。したがってテキストは推論時の入力にはできず、学習ターゲットの導出元としてのみ使える。
- レポートは 9 言語混在（英・西・仏・蘭・独・土・クロアチア/セルビア・希・ブルガリア）。
- ローカルのデータは**学習側は全件揃っている**: `train.csv` 4407 study、`train_series.csv` 24371 series で、`train_series/` 配下の実ディレクトリ数と一致する。dcm は 1 series あたり中央値30枚（11〜320）、1 study 合計で中央値162枚（67〜632）。
- `test.csv` / `test_series.csv` は 3 study・15 series のみ。これはダウンロード不足ではなくコンペ側のスタブ（採点対象のテストセットは非公開）。テスト側の規模を前提にしたメモリ見積りは無意味なので注意。
- ラベルが12列すべて揃っている study は **58 / 4407**。

### 既知の不整合（触るときは修正すること）

`notebooks/00_analysis/count_label_exist.py` は
(1) `ROOT` が macOS の絶対パス `/Users/thamada/...` にハードコードされている、
(2) 存在しない `data/mini_dataset/train.csv` を読む、
(3) `LABELS` に `"Effusion"` が重複していて 13 要素ある。
このノートブックを再実行・流用する際は上記を直す。新しいノートブックでは絶対パス直書きを避ける。

## ドキュメントと GitHub Wiki

`docs/wiki/` 配下の **`.md` ファイル**が GitHub Wiki に自動同期される（`.github/workflows/sync-wiki.yml`、`main` / `dev` への push で起動）。

- Wiki ページタイトル = `docs/wiki/` からの相対パスの `/` を `-` に置換したもの（`01_前処理/データ取得.md` → `01_前処理-データ取得`）
- ファイル名が `[private]` で始まるページは同期対象外
- `docs/wiki/` に無いページは Wiki から**削除される**
- `scripts/workflows/sync-docs-to-wiki.js` は GitHub Actions 環境でのみ実行可能（ローカル実行はガードで拒否される）。ローカルから Wiki を触ろうとしないこと
- 拡張子 `.md` が無いファイルは同期されない（`docs/wiki/01_前処理/データダウンロード（最小限）` が該当。同期したいならリネームが必要）

ドキュメントの編集は必ず `docs/wiki/` 側で行う。Wiki を直接編集しても次回同期で上書きされる。

## 参照ノートブックの設計知見

`notebooks/10_reference/training/pilkwang_kim/rsna-knee-baseline-v1.ipynb` は、このリポジトリが目指す 2.5D パイプラインの設計根拠が書かれた参照実装。方針を決める際はここを読む。要点:

- **スロット設計**: 撮像面（sagittal / coronal / axial）× 流体強調 × 脂肪抑制 で最大 6 スロット。DICOM ヘッダの TR/TE・`SeriesDescription` 等から weighting と fat-sat を再推定する（`train_series.csv` の 2 フラグは全行で一致しており実質 1 軸しか持たないため）
- **物理スケール正規化**: ピクセル数固定のリサイズではなく、130 mm の物理範囲でクロップしてから P ピクセルへリサンプル。半月板断裂（1〜3 mm）を残すには Nyquist 条件 `s_eff ≤ d/2` が要る（224 px → 0.580 mm/px は不足、336 px → 0.387 mm/px）
- **キャッシュ**: I/O 律速のため、スロット画像を一度だけデコードして uint8 でメモリ常駐。サイズは解像度の**二乗**で増える
- **ヘッド**: 12 診断それぞれが専用クエリでスロットに attend（欠損スロットは softmax からマスク）。study 単位のラベルしかないため、ヘッドは意図的に小さく保つ
- **バリデーション**: 同一レポートが複数 study で byte 一致するため、**レポート文字列のハッシュで分割**してリーク（同一グループの分断）を防ぐ

## 秘匿情報

`.env`（gitignore 済み、`.env.example` が雛形）に `KAGGLE_API_TOKEN` を置く。
