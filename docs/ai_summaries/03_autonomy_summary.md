# Autonomy — AI 向け要約

*原本*: docs/ESDE_Autonomy_Report.md (749 行)
*要約時点*: v9.9 完了前 (2026-04-11)
*対象読者*: 未来の Claude

---

## このフェーズが答えた問い

「少数の強い支配者」から「多数の弱い共存者」への相転移は何か。単一主体が自律的に存在する条件は何か。**答**: n→n+1 差分 (次元上昇) が質的相転移を引き起こす。5-node が差分の転換点。

## 用語 (このフェーズで導入されたもの)

- **label**: frozenset で生成時の主張を固定。死ぬまで解放しない (位相周波数グループの意思表示)。**魂**。
- **territory**: label の場の性質。oasis/penalty 比率が全サイズ一定 1.3×。サイズ非依存。
- **density independence**: 環境に依存せず自分で存在条件を作る能力。5-node で獲得。
- **Future** (= n→n+1 差分): 上位機能次元が下位に対して持つ新行動可能性。
- **2 つのフェーズ**:
  - 2→5「手放す」 (alignment 低下、share 喪失、density independence 獲得)
  - 6→9「取り戻す」 (retain 回復、territory 保持)
- **Lifecycle Instrumentation** (v8.1 以降): label 死亡監視、island 検出。

## 確定したこと

- **v8.0-v8.4**: 48-seed 51,163 labels。Lifecycle instrumentation で label 死亡監視と island 検出を確立。
- **Territory は場の性質**: oasis/penalty 比率が 2-node から 9-node まで全て 1.3× 一定 (サイズ非依存)。
- **全 n→n+1 が質的相転移**:
  - 2→3 生存率
  - 3→4 寿命
  - 4→5 density independence
  - 5→6 alignment 最低
  - 6→7 retain 回復
  - 7→8 territory 保持
  - 8→9 territory 支配
- **5-node の非還元的差分**: 「どこでも生きられる」(density independence)。環境に依存しない唯一のサイズ。
- **Collapse は ecology 内部崩壊ではなく物理層消滅による連鎖消滅** (A=1.0 時: links 2966→19、全滅)。
- **Trio は高密度領域の副産物**: suppression は density-driven (占有率支配)、trio 固有作用なし。

## サイズ別の質的差異

- **2-3 node**: 短命 (3-38 win)、環境依存、align 高 (0.60)
- **4 node**: 長寿命開始 (58 win)、密度非依存化の閾値
- **5 node**: 最適主体。age 98 win、density independent、share_retain 最低 (0.537)
- **6+ node**: 超長命 (190+ win)。6 で align 最低 (0.181)、7-8 で retain 回復 (0.74)、territory 保持開始

## 却下された方針

- **v8.1b**: E4 hardcoded → Constitution 修正で撤去
- **v8.1c**: S≥0.20 条件 → 圧縮発動、偽信号 -16%
- **v8.2A**: vacancy birth filter (「余白＝生存有利」は Claude の誤解釈) → 撤回
- **200win**: share_retain 3 相構造 (6+ で retain > 1.0) → 500win で全サイズ < 1.0 の偽信号と確定。5-node が真の底
- **α 感度テスト**: trio は「数量」に α 依存 (77% 減) だが「性質」は α 非依存。sole survivor は条件次第で標準形態

## 核心的発見

1. **frozenset 制約により label は移動しない**。「移動に見える」のは選択的生存。birth 時に主張を固定、以後不変。

2. **2 つのフェーズ の転換点 = 5-node**。下位 (2→5) は「失う」ことで環境依存から脱却。上位 (6→9) は「回復」することで territory 支配に至る。全遷移が質的相転移。

3. **物理層は床。崩壊は ecology の内部危機ではなく、物理層 links が 19 に落ちた瞬間の連鎖消滅。** A=0.7 でも仮想層は機能 (縮小するが生存)。

4. **環境変動と逆相関**。好況 (リンク増) = 競争激化 = label 減。不況 = 既存 label 温存。好況期に 2-node は全滅、4-5-node はむしろ有利。

5. **territory は「場」、リンクは「主体」の別物**。territory oasis/penalty 比率は全 n で 1.3× だが、ノードリンク比率はサイズ依存 (3-node 2.9× → 7-8 node 1.3×)。大きい label ほど penalty 側も物理的に機能。

## 次フェーズ (Primitive) への橋渡し

Autonomy で確定した「n→n+1 差分」と「5-node の転換点」は、Primitive (v9.x) での「原始的主体性の出現」を予兆する。差分を「主体の層化」として見ると、どの n から「判断・意図」が立ち上がるか。Taka の「自我は差分を保持することで立ち上がる」仮説。観測的には、7→8→9 の territory 保持フェーズで retention と coherence が加速度的に上昇。意味づけは保留、観測を継続。

## 原本を読むべきタイミング

- n→n+1 差分の具体的内容を知りたいとき
- territory がなぜ「場」なのかを理解したいとき
- 物理層 vs 仮想層の関係性を確認したいとき
- label ecology と環境変動の逆相関メカニズムの詳細を追跡したいとき
