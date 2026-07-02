# v1304a — dense 源での Stage 1B 再 smoke + Stage 2 smoke（Taka 指示ツリーの実行・停止）

*作成*: 2026-07-01、Code A。**Taka 指示（dense θ源探索→見つかれば Stage 1B 再smoke で washout を fair 確認→washout なら Stage 2）の実行。read-only・親へ feedback なし・物理非書込・停止（full/判定に進まない）・#12。**
*成果物*: `v1304a_smoke_dense.py` / `v1304a_stage2_smoke.py` + `outputs/v1304a_smoke_dense_*` / `v1304a_stage2_*`。

---

## 0. 結論（先に）
- **dense θ角度源が見つかった**：`original_phase_sig`（228/228・v11_m_c_phase_sig と 45重複で循環角度差 0.000＝完全な dense 版）。
- **Stage 1B 再smoke（coverage 1.0・fair）で washout は本物と確認**：初期θの shape は構造に痕跡を残さない。
- **Stage 2（構造 knob も attention から）も親特異な乖離を出さず**：plb（意味ある channel）はほぼ動かず、k_sync は動くが generic（親特異でない）＋幻チャネル。
- **構造的理由**：親 attention の**分布**を scalar knob 1 個に集約すると母平均に潰れ、v1302 の per-CID transfer（Mantel 0.62）を担った per-cid 変動が消える。→ 次の判断材料（判定は Taka）。

## 1. dense θ源（coverage 制約の解消）
| | v11_m_c_phase_sig（従来） | original_phase_sig（新） |
|---|---|---|
| coverage | 45/228（疎） | **228/228（dense）** |
| 45 重複の一致 | — | 循環角度差 median=max=**0.000**・range 同一 ＝完全な dense 版 |
| eye 別 attention mass の載る割合 | 16–22% | **全 eye 1.0** |

## 2. Stage 1B 再smoke（dense・fair）— washout は本物
coverage 1.0 で 4群×正式4eye×K6 を再走。parent−canon 差 vs canon の seed 間 std（noise 床）：
- **link_density / R_density / alive_ratio**：parent−canon = **0.0000**・group_range = **0.0000**（t_mid/t_late とも全群 byte 同一）＝初期θは構造 knob（plb/K_sync/N を全群同一固定）に一切効かない。
- **sync_order / n_labels / label_density**：parent−canon は noise 床**以下**（例 t_late now sync 0.056 vs noise 0.052、n_labels 0.67 vs noise 4.5）。
- ⇒ **coverage を潰しても初期θのみの shaping は t_mid/t_late で構造差を残さない（washout 本物）**。機構的にも当然（構造を決める knob を全群同一に固定し初期位相だけ変え、位相は Kuramoto で再編成）。v1302「継承は初期条件経由でなく持続 param 経由のみ」と整合。

## 3. Stage 2 源の dense 探索（非対称）
| knob | 源（cw_run） | dense twin | 判定 |
|---|---|---|---|
| **k_sync** | v11_m_c_r_core（45疎） | **v18_v_unified_concentration_birth（228・r=1.0・同range）** = 完全 dense twin | ただし v1302 で **k_sync←r_core は幻チャネル**（#CW6・単独 n.s.） |
| **plb** | v11_m_c_s_avg（45疎） | **なし**（最良 current_social 0.36） | v1302 で **transfer 本体は plb←s_avg** ＝意味ある方が疎のまま |

## 4. Stage 2 smoke（構造 knob も attention から・scalar は加重平均）
scalar knob ゆえ shaping は「分布」でなく attention 加重平均（engine が scalar を取る）。θ は dense shape（Stage 1B）を維持。

### 4.1 群別 knob（動いたか）
- **plb はほぼ動かない**：全 eye・全群で **0.00692–0.00718（±2.5%）**（canon 0.007）。attention 加重平均 s_avg ≈ 母平均ゆえ z≈0。s_avg coverage は 16–22%（bgen のみ 1.0）。
- **k_sync は動く**：canon 0.1 → 非canon 群 ~0.19–0.27。ただし parent≈shuffle≈uniform（非canon 群が互いに同程度）。

### 4.2 親特異性（parent が shuffle/uniform を超えるか）
- **sync_order（t_late 群平均）**：canon 0.081／parent 0.115–0.215／shuffle 0.192–0.254／uniform 0.213–0.239。**parent は shuffle/uniform を超えず、むしろ低い側**（now parent 0.115 < shuffle 0.254）。＝sync 上昇は「非canon vs canon」の **generic** 効果（k_sync が canon より高い）で、**親特異でない**。しかも k_sync は幻チャネル。
- **link_density / R_density / label_density**：parent−canon は noise 床以下（link parent−canon ≤0.022 vs noise 0.055）。uniform は canon と同一（0.734）。＝構造は分離せず。
- ⇒ **Stage 2 も親特異な構造乖離を出さない**（3条件②を満たす兆候なし・smoke first-look）。

## 5. なぜ立たないか（構造的理由・要 Taka/Web Claude 判断）
- v1302 の生きた transfer（plb←s_avg・Mantel 0.62）は **CID ごとに 1 子（各子が自分の s_avg から自分の plb）** で成立した＝per-cid 変動が信号。
- v1304a は親 attention の**分布**を **1 子（群あたり scalar knob 1 個）** に集約するため、plb = attention 加重平均 s_avg ≈ **母平均に潰れ**、群間差が消える（parent も shuffle も uniform も似た平均）。
- つまり **scalar knob への集約（Stage 2）は、v1303 で残した「目ごと分布」と v1302 の「per-cid 変動」の両方を潰す**。Stage 1（θ分布 shape）は残すが washout、Stage 2（knob）は残らず集約で潰れる、という板挟み。
- **候補（判定は Taka/Web Claude）**：(i) 親 attention 分布を保つには **per-cid ensemble**（Code A 旧候補 B＝attention で重み付けた per-cid 子群を canon と比較）に戻す＝v1302 の per-cid transfer を attention 重みで再現する路線（ただし設計は Stage 1 で B を「shaping を測れない」と退けた・構造 transfer には B が要るかもしれない）。(ii) plb の dense 源が無い制約を受け入れ 45 支持で per-cid ensemble。(iii) この段では「子は別系として立たない（出口 c 寄り）」と読む。

## 6. 実施範囲・停止
- 実施：dense 源探索・Stage 1B 再smoke（96run）・Stage 2 源探索・Stage 2 smoke（96run）。いずれも seed0・K6・first-look・read-only・親へ feedback なし・物理非書込。
- **していない**：3条件の分布距離統計・per-t 乖離推移・n_core 層化・other-parent null・分散/検定・成立判定（#12）。
- Taka 指示ツリー（dense→再smoke→Stage 2）を実行し、Stage 2 も親特異乖離を出さなかった所で**停止**。次（per-cid ensemble に戻すか／出口 c と読むか）は Taka/Web Claude 判断。

## 7. 一文サマリ
v1304a dense再smoke+Stage2（Taka指示ツリー実行・read-only・停止・#12）── dense θ角度源 original_phase_sig(228・v11_m_c_phase_sig の完全 dense版・角度差0.000)が見つかり coverage 1.0 で Stage 1B を fair 再smoke した結果 **washout は本物**(link/R/alive は parent−canon=0・sync/n_labels は noise床以下＝初期θは構造 knob 固定下で痕跡を残さず・v1302「持続param経由のみ」と整合)、指示通り Stage 2(構造 knob も attention から)へ進むと **k_sync 源は dense twin(v18_concentration r=1.0)あるが幻チャネル・plb 源 s_avg は dense twin なしで意味ある方が45疎のまま**、Stage 2 smoke は **plb がほぼ動かず(±2.5%・加重平均 s_avg≈母平均)・k_sync は動くが generic(非canon 群互いに同程度)で parent は sync_order で shuffle/uniform を超えず(むしろ低い)・link/R は noise内=親特異な構造乖離なし**、構造的理由は **親 attention の分布を scalar knob 1個に集約すると母平均に潰れ v1302 の per-cid transfer(Mantel0.62)を担った per-cid 変動が消える**(Stage1 は分布 shape 残すが washout・Stage2 は集約で潰れる板挟み)、次候補=per-cid ensemble に戻す/45支持で受ける/出口c と読む は Taka 判断、smoke first-look ゆえ 3条件統計・成立判定は置かない。
