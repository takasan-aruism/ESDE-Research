---
name: parallel execution before confirmation
description: Do not run heavy simulation scripts without confirming execution strategy (parallel, step_window, etc.) with user first
type: feedback
---

重い計測スクリプトを勝手に実行しない。実行前にユーザーに確認を取る。

**Why:** ESDE の long run は 1 seed あたり 2 時間超かかる場合がある。v910 long run は元々 `parallel -j5` で並列実行されている。手動 step ループで逐次実行すると 5 seeds × 2 時間 = 10 時間以上かかる。ユーザーに確認すれば `step_window()` 利用や `parallel` 実行など適切な方法を選べた。

**How to apply:**
- 計測/シミュレーションスクリプトを書いたら、実行前にユーザーに見せて確認を取る
- 既存の実行パターン (parallel コマンド、step_window() の使用) を確認してそれに倣う
- 特に長時間かかる処理は「これで実行していいか」を聞く
