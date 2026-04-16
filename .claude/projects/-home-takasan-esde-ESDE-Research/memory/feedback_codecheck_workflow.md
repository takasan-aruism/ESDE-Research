---
name: codecheck document workflow
description: Always create codecheck request docs for code/scripts before execution. Separate Claude Code instance reviews and returns status.
type: feedback
---

コードやスクリプトを作成したら、必ず同一フォルダ内にコードチェック用ドキュメントを作成する。

**Why:** 別の Claude Code インスタンスがコードチェック担当としてレビューする運用。実行前にレビューを通すことで品質を担保し、勝手に長時間プロセスを走らせる等の問題を防ぐ。

**How to apply:**
1. コード作成時に `xxxx_codecheck_request.md` を同一フォルダに作成
   - コードの目的、設計、実行方法、依存関係、想定実行時間などを記載
2. 別の Claude Code がレビューし、ドキュメント内に直接コメントを入れる
3. レビュー完了後 `xxxx_codecheck_status_approved.md` または `xxxx_codecheck_status_denied.md` を作成
4. approved になるまで実行しない
