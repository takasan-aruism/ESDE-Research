# v1303j Step A 観察事実報告（selector・seed0・read-only・判定なし #12）

*作成*: 2026-07-01、Code A。**事実のみ・success/fail を置かない。(あ)(い)採否・distinct 読み・within_ncore 最終採否・cross-eye pull は Taka 領域。**

## 0. 構成
- alive grid: 73321 (cid,t) 行 / 228 cids / t∈[10,25000] step10
- grid/alive 出所: per_subject_seed0.csv（host_lost_step/birth_window）+ c_trajectory(window→step=500)。v1303i 非依存。

## 1. 目間 corr（§3.0 ゲート・auto-drop なし）
```
                  now_theta  persist_thetapct  link_rarity  bgen_pct  peer_theta  global_theta  within_cid_theta
now_theta            1.0000           -0.0576       0.1023    0.0009      0.3668        0.4846            0.3519
persist_thetapct    -0.0576            1.0000       0.0948    0.0150      0.3235        0.0780            0.3450
link_rarity          0.1023            0.0948       1.0000   -0.0002      0.0999        0.0897            0.0909
bgen_pct             0.0009            0.0150      -0.0002    1.0000     -0.0126        0.0066            0.0004
peer_theta           0.3668            0.3235       0.0999   -0.0126      1.0000        0.9121            0.9876
global_theta         0.4846            0.0780       0.0897    0.0066      0.9121        1.0000            0.9025
within_cid_theta     0.3519            0.3450       0.0909    0.0004      0.9876        0.9025            1.0000
```
- 注: matrix は substrate 依存（事前調査 付録 A: within_ncore×瞬間θ は exact 0.83 / asof 0.37）。distinct 読みは Taka。

## 2. pull 系列の sanity（目別 distinct cid・fallback 率・eligible）
```
             eye                                                       label  n_t  distinct_pulled_cid  fallback_uniform_rate  mean_eligible_count  mean_alive_count
       now_theta                           瞬間θ(f raw theta_resultant_length) 2500                  209                    0.0                 24.8              29.3
persist_thetapct                                 持続θ(e theta_cid_percentile) 2500                  200                    0.0                 24.4              29.3
     link_rarity               link稀さ非θ(i rarity_internal_link_within_ncore) 2500                  208                    0.0                 24.8              29.3
        bgen_pct                      静的B_Gen(h bgen_pct_in_ncore・per-cid定数) 2500                   43                    0.0                 14.7              29.3
      peer_theta peer-rel θ(i rarity_theta_within_ncore・prove-by-trajectory) 2500                  212                    0.0                 24.8              29.3
         uniform                                            uniform baseline 2500                  223                    0.0                 29.3              29.3
```
- 静的 B_Gen は per-cid 定数ゆえ distinct cid 数が少ない＝**期待挙動（degenerate を隠さず記録・「失敗」と書かない）**。
- B_Gen の fallback 率＝B_Gen 未定義 cid のみの t で uniform に落ちた割合（coverage 0.56 由来）。B_Gen pull は「全 CID 中」でなく「eligible 集合内で珍しい」と読む（rev3 §10-1）。

## 3. within_ncore（peer-rel θ）出口＝瞬間θと別軌跡か（rev3 §10-2）
- pulled-cid 一致率(瞬間θ, peer-rel θ) = 0.044
- 参考: 瞬間θ vs uniform 一致率 = 0.037 / chance(1/mean_eligible) = 0.040
- **⚠ Code A の正直な留保（この指標は弱い）**: single-draw（~25 cid から1本引き）の pulled-cid 一致率は、
  目が同一でも別物でも chance(≈0.040) に支配され、distinct 性を判定できない（peer も uniform も chance 付近）。
  rev3 §10-4「RNG 単発軌跡を読みすぎない」が実際に効いている。**distinct 性の情報は値 corr（§1: peer×瞬間θ asof 0.37）と
  cross-eye pct 側にあり、軌跡ベースの確定は many-RNG 集約（Step B）が要る**。Code A は一致率の事実と本留保のみ・判定は Taka。

## 4. 持続θ＝duration lens か（segment タグ・rev3 §10-3）
- 持続θ pull の segment_length: n=2500 / median=4.0 / max=49（タグ付き pull 割合 1.00）
- 長 segment に集中するかの読みは Taka。集中しなければ Archive lens の salience 要再考と記録。

## 5. 言える / 言えない
- **言える**: 珍しさ値に比例して pull した attention trajectory を目ごとに作った（read-only・seed0）。
- **言えない**: 「ESDE が注意した / 自律的に選んだ / 投影が始まった」。RNG 単発軌跡を唯一の注意と読まない（§10-4）。
- 出口＝目ごと attention trajectory（将来の投影＝応答方向の入力・先送り stub）。

## 6. 次段
- smoke seed0 まで。main・複数 seed には進まない。承認後に Step B（正式カラム化・複数 seed・RNG 安定性検査）。