# v10.3 設計論点 — Code A 第二次応答 (統合版受領後)

*作成*: 2026-04-30、Code A (実装担当)
*対象*: Claude (相談役) 統合版 v10.3 設計論点まとめ
*親資料*: `v102_v103_design_investigation.md` (第一次応答)、`v10_3_design_discussion_points.md` (Claude 統合版)
*用途*: §9.4 Q14-16 (Code A 質問) + 共通 §9.1 Q1-5 への応答

---

## 0. 統合版受領

Claude 統合版を受領。第一次応答の **Cat 3a 定義変更 (3a-i)**、**主役は世代横断型**、**案 X (別 CSV、最小限) 採用** などが反映されていることを確認。新規追加された **Integration 概念** (§3) と **観察対象の動的絞り込み** (§5) を踏まえて第二次応答を行う。

---

## 1. §9.1 共通質問 (Q1-Q5) への応答

### Q1. Integration 概念と v10.3 射程

**応答**: 認識共有可能、違和感なし。

実装担当として整理:
- v10.3 では **「Integration 立ち上がり前の素材集め」** に徹する
- 実装機構は双方向 E3 + 観察軸のみ追加
- 摂食順序問題は触らない (Integration 不在のため現状仕様維持で OK)
- v10.4 以降での Integration 独立化に向けた CSV を保持する形

「Integration が取った Q をどう分配するか」は v10.4 以降で扱うべき問題、v10.3 で前提条件を整える。これは Aruism「構造が先、意味が後」と整合。

### Q2. カテゴリ実装可否の過不足

**応答**: 過不足なし。

第一次応答で示した実装範囲:
- **既存 CSV から取得可**: 3a-i, 3b, 3c, 4b, 4c
- **v10.3 新規 logger で取得**: 1a, 1b, 1c, 2a, 4a
- **v10.3 見送り**: 2b, 2c (engine 拡張必要)
- **永久除外**: Cat 5 (cid 自己参照)

統合版の Cat 3a-i 採用 + Cat 2a/4a の新規 logger 方針 + 2b/2c 見送りは妥当。

### Q3. 動的検出の閾値

**応答**: 以下の試案を提案 (§5 で詳細)。

```
Stage 1 条件: n_core ≥ 4 ∧ n_consciousness ≥ 5
Stage 2 条件: Stage 1 cid と双方向 E3 を発火した相手も追加
Stage 3 条件: Stage 1/2 cid が双方向 E3 で第三項として参照した cid も追加
```

age 閾値は不要 (n_consciousness ≥ 5 が age を間接的に保証する。意識発動 5 回経験には数千 step 必要)。

別案として「c_first_increment_step ≤ 10000」を加えれば「主役確定済みかつ早期発動者」に絞れるが、過剰な絞り込みは観察事実を取りこぼすため **本案 (n_core + n_consciousness のみ) を推奨**。

### Q4. 観察目標の見落とし

**応答**: §7.6 (Integration 登場条件) の指標化に補足提案。

第一次応答 §6 で得た事前推定:
- 1 候補ペアあたり同時複数カテゴリ該当の分布 = 大半 1 カテゴリのみ (89.6%)、2 カテゴリ 0.7%、3 カテゴリ 0%

→ Integration 登場の前兆として **「1 双方向 E3 ペアに該当する第三項候補カテゴリ数」** が指標になる可能性。これを §7.6 に追加観察軸として組み込むことを提案:

> 同時複数カテゴリ該当ペアの window 別分布 / 主役ペアの平均カテゴリ該当数 / 「2 カテゴリ以上同時該当」ペアの世代距離分布

事前推定では 2 カテゴリ同時は稀 (0.7%) だったが、v10.3 機構実装後 (= 双方向 E3 で発火数が遥かに多くなる) に同時複数該当が増えるかは観察対象。

### Q5. 詰め残し論点

**応答**: 以下 3 点を提案。

#### Q5-A: shadow audit と本番 run の bit-identity 検証範囲

shadow audit (= C 消費なし、ログのみ) では物理層 + C 系列 + Q 系列が **すべて v10.2 baseline と完全一致** すべき。これは shadow audit の正当性検証として強力な制約。

論点 G (bit-identity 検証) の二層検証に **層 C** を追加提案:
- 層 C: shadow audit run の出力が v10.2 main と物理層 + C + Q + balance_decisions すべて bit-identical

本番 run では C 系列が変動するため層 B のみ。

#### Q5-B: 観察対象から「外れる」ケース

cid が動的検出条件を一度満たした後の挙動:
- 推奨: **一度 target に追加された cid は run 終了まで保持** (= 削除しない)
- 理由: 後で双方向 E3 発火するか、第三項として登場する可能性
- メモリは set で保持 (Q14 試算で十分軽量)

reaped (= 完全消滅) cid も target に保持してよい。reaped 後の発火はないため、自動的に記録されなくなる。

#### Q5-C: per_subject 追加列の事後計算 vs run 中蓄積

per_subject の追加列 (n_be3_total 等) は **run 中蓄積** を推奨:
- run 中: cid object に counter を持たせ、双方向 E3 発火時にインクリメント
- run 末: per_subject 出力時に counter を読んで列に書き込む
- 利点: 事後 join 不要、CSV 整合性高い
- 欠点: cid object に新規 counter 状態を追加 (Q-1 等の dynamic state 拡張なので Taka 規律に抵触しないが、要明示)

**規律解釈**: counter は「cid 内部の選択を実装するもの」ではなく「観察者が cid に紐づけて記録する集計値」。M_c (固定値) や Q/C (代謝量) と同列の扱い。Taka 確認推奨。

---

## 2. §9.4 Q14-16 (Code A 質問) への応答

### Q14. 動的検出の実装方針 + メモリ・I/O コスト

**応答**: 軽量、実装容易。

#### 実装パターン

```python
class ObservationTargetTracker:
    """v10.3 動的観察対象追跡。
    
    Stage 1: 主役条件 (n_core ≥ 4 ∧ n_consciousness ≥ 5) で逐次追加
    Stage 2: 双方向 E3 partner も追加 (= cid_a or cid_b が target なら相手も)
    Stage 3: 第三項として参照された cid も追加
    """
    def __init__(self):
        self.target_ids: set[int] = set()
        self.added_at_step: dict[int, int] = {}
        self.added_via: dict[int, str] = {}  # 'stage1' / 'stage2' / 'stage3'
    
    def stage1_check(self, cid: int, n_core: int, n_consciousness: int,
                     current_step: int) -> bool:
        """主役条件チェック (双方向 E3 イベント発火時に呼ぶ)"""
        if cid in self.target_ids:
            return True
        if n_core >= 4 and n_consciousness >= 5:
            self.target_ids.add(cid)
            self.added_at_step[cid] = current_step
            self.added_via[cid] = 'stage1'
            return True
        return False
    
    def stage2_propagate(self, cid_a: int, cid_b: int, current_step: int):
        """双方向 E3 発火時、片方が target なら相手も追加"""
        a_in = cid_a in self.target_ids
        b_in = cid_b in self.target_ids
        if a_in and not b_in:
            self.target_ids.add(cid_b)
            self.added_at_step[cid_b] = current_step
            self.added_via[cid_b] = 'stage2'
        elif b_in and not a_in:
            self.target_ids.add(cid_a)
            self.added_at_step[cid_a] = current_step
            self.added_via[cid_a] = 'stage2'
    
    def stage3_propagate(self, cid_c: int, current_step: int):
        """第三項として参照された cid を追加"""
        if cid_c not in self.target_ids:
            self.target_ids.add(cid_c)
            self.added_at_step[cid_c] = current_step
            self.added_via[cid_c] = 'stage3'
    
    def is_target(self, cid: int) -> bool:
        return cid in self.target_ids
```

#### コスト試算 (Code A 既存データから)

実データで事前シミュレーション (N=5000、24 seeds 合計):

| Stage | cid 数 | 全 cid 比 | per seed mean |
|---|---:|---:|---:|
| Stage 1 (主役のみ) | 272 | 5.2% | 11.3 |
| Stage 2 (+ E3 partner) | 354 | 6.8% | 14.8 |
| Stage 3 (推定 +20%) | ~417 | ~8% | ~17 |

メモリコスト:
- target set: ~500 cid × 8 bytes (int) + 30 bytes overhead = **~15 KB / seed**
- added_at_step / added_via dict: 同程度 = **~30-50 KB / seed total**

I/O コスト:
- per-step lookup: O(1) dict access × 数十 ns
- per-event filter: target に含まれない pair はログしない → ログ量が 92% 削減

判定: **メモリ/I/O コスト極小**、実装容易。

注意: Stage 2 の試算は strict simultaneous onset partners のみ (= 1,552 ペア)。実際の双方向 E3 では「同 step 同 link 共有」全部が partner になるため、Stage 2 cid 数は実際 **500-800 cid に膨らむ可能性**。それでも全 cid の 10-15%、許容範囲。

### Q15. 3 つの CSV logger の実装複雑度

**応答**: 中程度、依存関係あり。

#### logger 別評価

| logger | 列数 | 行数想定 (N=5000) | 実装複雑度 | 依存関係 |
|---|---|---|---|---|
| **bidirectional_e3_log** (本流) | ~30 | ~12,500/seed | 中 | event_emitter hook |
| **bidirectional_e3_3rd_cid_log** (sub 1) | ~10 | ~500/seed | 低 | post-process 必要 |
| **bidirectional_e3_member_nodes_log** (sub 2) | ~10 | ~12,500/seed | 中 | engine state read |

#### 実装上の論点

**論点 i**: 本流の has_3rd_cid_* フラグはリアルタイムで判定不可

理由: closed triad (Cat 1a) 検出には「window 内の他のペア」を知る必要がある。リアルタイムでは判定不可。

**Code A 推奨**: 本流は raw event のみ記録 (has_* フラグは空欄)、window 末で post-process して埋める。または run 末に集計スクリプトで埋める。これで実装複雑度は **本流: 低、post-process スクリプト: 中** に分解できる。

**論点 ii**: bidirectional_e3_member_nodes_log の frozenset 文字列化

member_nodes は frozenset of int。CSV に書くには文字列化が必要。

```python
member_nodes_str = "|".join(str(n) for n in sorted(member_nodes))
```

事後解析でパース: `set(int(x) for x in s.split("|"))`。

サイズ: 平均 n_core ≈ 3 ノード、最大 ~10 ノード。各ノード ID 4 桁 → 1 行 ~50 文字 × 12,500 行 = 600 KB/seed = 14 MB/24 seeds。許容範囲。

**論点 iii**: per_subject 追加列の埋め方

run 中蓄積 (Q5-C で論じた) を採用すれば post-process 不要。

#### 実装複雑度総評

| 段階 | 工数感 |
|---|---|
| 双方向 E3 機構実装 (event_emitter 拡張) | **3-5 日** |
| 観察対象 tracker 実装 | **1 日** |
| 3 つの logger 実装 | **2-3 日** |
| post-process スクリプト (has_* フラグ等) | **1-2 日** |
| smoke + bit-identity 検証 | **1-2 日** |
| **合計** | **8-13 日** |

Code A 単独実装で 1.5-2 週間想定。これは v9.14 paired audit 実装と同程度のスケール。

### Q16. smoke 段階で観察対象規模を試算する方法

**応答**: 以下 4 つの metric で判定。

#### 試算 metric

```
M1: target cid 数 / 全 cid 数 ≤ 15%
M2: bidirectional_e3_log 行数 / step ≤ 10
M3: smoke 出力 CSV サイズ ≤ 200 MB (10 windows smoke で)
M4: smoke wall time / 期待値 ≤ 1.3 (= 30% overhead 以内)
```

#### smoke 設定

| 項目 | 値 |
|---|---|
| seeds | 1 (smoke 確認用) |
| N | 2500 (cost と現実性のバランス) |
| maturation | 5 (短縮) |
| tracking | 10 (短縮) |
| window_steps | 500 |
| 想定 wall time | ~5-10 min |

#### 判定フロー

1. smoke run 実行
2. M1-M4 を測定
3. 全部 ≤ 閾値 → 本番 run 進行
4. M1 が超過 → 動的検出条件を厳格化 (n_core ≥ 5 など)
5. M2 が超過 → 観察対象から非主役ペアを除外
6. M3 が超過 → frozenset 文字列化を最適化、または Cat 2a/4a logger を別 smoke に
7. M4 が超過 → C 消費の per-step オーバーヘッド見直し (蓄積を window 末に集約)

#### 試算予想 (現データから)

| metric | 予想値 | 判定 |
|---|---|---|
| M1 (target 比) | 8% (Stage 3) | ✅ 余裕 |
| M2 (events/step) | ~0.5-2 | ✅ 余裕 |
| M3 (CSV size) | ~50 MB | ✅ 余裕 |
| M4 (wall ratio) | ~1.2 | ✅ 余裕 |

→ **smoke は問題なくパスする見込み**。

---

## 3. 補足: 第一次応答からの修正・追加

### 3.1 Cat 3a-i の実装詳細

第一次応答で「両者が同 cid (現 ghost) と E3_contact 経験あり」を提案。実装方針:

```python
def has_shared_e3_contact_cid(cid_a, cid_b, current_step,
                               e3_history: dict[int, set[int]]) -> tuple[bool, list[int]]:
    """両者が過去に E3_contact した cid 集合の intersection が空でないか。
    
    e3_history[cid] = この cid が E3_contact した相手 cid 集合
    返り値: (該当あり, 共通 cid のリスト)
    """
    contacts_a = e3_history.get(cid_a, set())
    contacts_b = e3_history.get(cid_b, set())
    shared = contacts_a & contacts_b
    return (len(shared) > 0, sorted(shared))
```

run 中に e3_history を逐次蓄積 (= 各 cid の過去 E3 partner set)。メモリは ~5000 cid × 数十 partner = ~250 KB/seed。

「現 ghost」フィルタを追加するなら `host_lost_window` で絞る。または **「過去 E3 partner で現在 ghost のもの」のみカウント**。判断は Taka 預け。

### 3.2 Stage 2 の実装上の注意

Stage 2 (E3 partner も追加) を実装すると、target cid 集合が単調増加する。一旦増えたら減らない。これは:
- 利点: 過去の発火を取りこぼさない
- 欠点: 主役じゃない cid (たまたま主役の partner だった) もログされる

これにより、観察データに「主役の周辺 cid」が含まれる。これは「主役の活動圏」を観察する意味で有意義。

ただし「**完全に主役のみに絞りたい**」なら Stage 1 のみで実装。判断は Taka 預け。

### 3.3 計算コスト試算の更新

第一次応答で示した N=10000 で +20-30% wall time を再確認:

- 双方向 E3 検出: per-step link 走査 + alive 確認 → **+5%**
- C 消費 + 観察対象 filter: per-event 処理 → **+5%**
- 第三項 post-process (window 末): one-time per window → **+10-15%**
- CSV 書き出し (3 logger): I/O → **+5%**
- 合計: **+25-30%**

N=10000 で v10.2 wall 9.6h → v10.3 で **~12-12.5h** 想定。

---

## 4. 推奨と次のステップ

### 4.1 v10.3 実装の暫定設計 (Code A 第二次応答後)

1. **新規 CSV**: 案 X 採用 + 3 logger (bidirectional_e3_log + 3rd_cid + member_nodes)
2. **新規 logger**: per-step flush、event_emitter hook 経由
3. **動的観察対象 tracker**: ObservationTargetTracker クラス、Stage 1+2+3
4. **B-1 採用**: 両者 C ≥ 1 必須 (自然フィルタ)
5. **shadow audit 必須**: C 消費なしで先に挙動確認、層 C bit-identity 検証
6. **post-process スクリプト**: has_3rd_cid_* フラグを window 末に埋める
7. **per_subject 追加列**: run 中 counter で蓄積 (要 Taka 規律確認)

### 4.2 観察スケール推奨

維持:
- **本番**: N=5000 (主役 270 cid、wall ~12-15h with v10.3 overhead)
- **追試**: N=10000 (主役 310 cid、wall ~12-13h)
- **smoke**: N=2500、tracking 10、1 seed (wall ~10-15 min)

### 4.3 提案する Smoke→Shadow→本番の進行

| 段階 | 設定 | 目的 | 想定 wall |
|---|---|---|---|
| smoke 1 | N=2500、tracking 10、1 seed | 機構動作確認、bit-identity 層 A | ~15 min |
| smoke 2 | N=2500、tracking 10、24 seeds | 観察対象規模試算 (Q16 の M1-M4) | ~30 min |
| **shadow audit** | **N=5000、tracking 50、24 seeds、C 消費なし** | **層 C bit-identity 検証 + 観察データ収集** | **~3-4 h** |
| 本番 N=5000 | N=5000、tracking 50、24 seeds、C 消費あり | 本番観察 | ~13-15 h |
| 追試 N=10000 | N=10000、tracking 50、24 seeds | 再現性確認 | ~12-13 h |

合計 wall: 約 30 時間 (1 日半)。

### 4.4 実装スケジュール (Code A 単独)

| 期間 | 内容 |
|---|---|
| 1-2 日目 | event_emitter 拡張 (双方向 E3 検出) |
| 3 日目 | ObservationTargetTracker 実装 |
| 4-5 日目 | 3 logger 実装 |
| 6 日目 | 単体テスト + smoke 1 |
| 7-8 日目 | post-process スクリプト + smoke 2 |
| 9 日目 | shadow audit 設計 + 実行 |
| 10 日目 | shadow audit 結果分析 |
| 11-12 日目 | 本番 run + 追試 (放置で 30h) |
| 13-15 日目 | 結果解析 + レポート |

---

## 5. 結論

統合版 v10.3 設計論点まとめ受領、Code A 第二次応答完了:

### 5.1 §9.1 共通質問 (Q1-Q5) への応答

- **Q1 Integration**: 認識共有 OK、v10.3 では並存記録に留める
- **Q2 カテゴリ過不足**: なし
- **Q3 動的検出閾値**: n_core ≥ 4 ∧ n_consciousness ≥ 5 を推奨
- **Q4 観察目標見落とし**: 同時複数カテゴリ該当の分布を §7.6 に追加提案
- **Q5 詰め残し**: bit-identity 層 C 追加、observation target の保持戦略、per_subject 蓄積戦略

### 5.2 §9.4 Code A 質問 (Q14-Q16) への応答

- **Q14 動的検出コスト**: メモリ ~50 KB/seed、I/O 軽量、実装容易
- **Q15 3 つの logger 実装**: 工数 8-13 日、post-process 分離で複雑度低減
- **Q16 smoke 規模試算**: 4 metric (M1-M4) で判定、N=2500/tracking 10/1 seed で 15 min smoke

### 5.3 試算結果

実データから事前シミュレーション (N=5000):
- 観察対象規模 Stage 1: 272 cid (5.2%)
- Stage 2: 354 cid (6.8%)、Stage 3 推定: ~417 cid (8%)
- v10.3 機構実装後の Stage 2 は実際 500-800 cid (10-15%) と推定

### 5.4 出力

```
developmental/v102/v102_v103_design_response_v2.md (本ドキュメント)
```

CSV / スクリプト追加なし (試算は本ドキュメント内の bash one-liner で実行)。

---

## 6. 推奨される次のアクション

1. 本第二次応答を Claude (相談役) 統合版にフィードバック
2. Gemini Architect / GPT Auditor の応答を併せて Claude が統合
3. Taka 承認 → v10.3 主題ドキュメント着手
4. 主題ドキュメント承認 → Code A 実装指示書作成
5. 実装開始 (smoke 1 から、§4.4 スケジュール)

---

*以上、Code A 第二次応答 (統合版受領後)。*
