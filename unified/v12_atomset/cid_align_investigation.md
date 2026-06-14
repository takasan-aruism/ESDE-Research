# v12 — cid_align 案の実コード検討 + offline プロトタイプ「実際こうなりました」

日付: 2026-06-14 / Web Claude 案「各 CID に物理(θ)と別次元の48次元 Atom 座標 cid_align を持たせ、経験で Atom に寄せる」を実コードで検討＋プロトタイプ。Taka「言うは易し、使えるものとして動くにどうするか」。

## 0. 結論（先に・正直に）

- **cid_align 案 ≈ 既に実装した `align` チャネル**（cid_align_dir: 48次元・cid_full_vec で init・α·f·exp_dir で更新・正規化・θ 非書込）。新規発明でなく既存。
- **核心主張「decouple」は正しい**：cid_align は θ 独立 → **物理を回さず経験ストリームだけで offline 計算できた**（プロトタイプで実証）。
- **プロトタイプ結果（offline、v107 経験ストリーム）**：
  - Atom 一致率は経験で**上がる**（67-71% の CID、個別 CID0 0.48→0.62）＝「寄る」機構は動く。
  - 一致率の**上がり量は cid 特異でない**（real≈shuffle、real>shuffle ~47%＝偶然）＝どんな経験でも align は鋭くなる(tautological)。
  - **だが「どの atom に向くか(行き先)」は cid 特異**：own vs 他人で end atom が **84-87% で異なる**＝行き先は自分の経験が決める。
  - **行き先は多様（27-28 種の atom）**＝各 CID が別 atom に向く＝**個性化（収束/淘汰でない）**。
- **→ Atom 空間では個性化が成立**：各 CID が自分の経験で固有の atom に寄り、多様に分かれる。chaos に攪乱されない（物理独立）。**Taka の「CID が Atom に寄る」目的は Atom 空間で達成**。
- **残る本丸＝出口（Atom→物理）**：cid_align は意味ある cid 特異・多様な Atom 座標になったが、**それが CID の物理的振る舞いを変えるか（出口）が未解決**。これが「使えるか孤立か」を分ける（Web Claude が釘刺した弱点そのもの）。

---

## 1. 検討点(1): cid_align と物理の接続

- **入口(物理→Atom, init)**: 既存 `cid_full_vec`（cog の構造から48次元）で init。物理素性が出発点＝紐づく ✓。
  - 注: v106 `build_cid_vector` は run-end (seed_max/C_at_run_end 依存)＝**live 使用不可**。live は cid_full_vec が正しい（既存）。
- **出口(Atom→物理)**: ここが crux。align チャネルの出口（出力 exc 重み + 入力 addressing）は**弱かった**（実測 corr_C≈corr_F、入力分布ほぼ不変）。Web Claude 案の torque_factor 係数も、align の出口同様に弱いと**孤立した二つの系**になる。**出口の強さが使えるか孤立かを分ける（未解決）**。

## 2. 検討点(2): exp_vec(経験の48次元化)

- `build_cid_vector` は run-end → 不可。**`cid_full_vec`（live、cog 状態を semantic 領域へ）が使える**（既存）。プロトタイプは v107 *_pre から同型の48次元を構築（lifespan/n_core/familiarity/C/n_alphas/n_observed を temporal/scale/epist/ontol/intercon/resonance へ）。

## 3. 検討点(3): core channel からの移行コスト

- **低い**。`align` チャネルが既に cid_align_dir を持つ。移行＝(a) Atom 一致率を直接測る計装を足す（生存でなく）、(b) 出口を torque_factor 係数に、(c) shuffle を「どの経験が align を更新するか」に置く（現 align は出口で shuffle、cid_align の検証には更新側 shuffle が要る）。

---

## 4. プロトタイプ「実際こうなりました」(cid_align_prototype.py、物理を回さず offline)

| seed | 一致率gain real/shuffle | real>0 | 行き先 own≠他人 | 行き先多様性 |
|---|---|---|---|---|
| 0 | +0.027 / +0.027 | 67% | 84% | 28種 |
| 1 | +0.030 / +0.032 | 71% | 86% | 27種 |
| 2 | +0.026 / +0.028 | 69% | 87% | 27種 |

- decouple 実証（offline 計算）。一致率は上がる。上がり**量**は非cid特異(generic sharpening)だが、**行き先 atom は cid 特異(85%)かつ多様(28種)＝個性化**。

## 5. 提案（Taka/Web Claude へ）

- **cid_align は Atom 空間の cid 特異・多様な identity として成立**（「寄る」目的達成、chaos 非攪乱、offline 計算可）。これは前進。
- **次の本丸は出口**：この cid 特異な Atom 座標を、CID の物理的振る舞いに**どう効かせれば孤立しないか**。align の出口（exc重み/addressing）は弱かった。torque_factor 係数で、cid_align の行き先 atom が「どの近隣を引き寄せるか」の選択性に効かせる線（Taka『phase_sig は familiarity に接続』）を、出口接続の強さを測りながら試す。
- **検証**：出口を繋いだ時、(a) CID の振る舞い（生存/構造）が cid_align の行き先で cid 特異に変わるか、(b) shuffle で消えるか、(c) 物理 θ に書かない（grep 確認）。**ただし decouple の代償＝出口が弱いと孤立**、を測りながら。

## ファイル
- `cid_align_prototype.py`（offline 検証、物理非依存）
- 既存: `m5_substrate_atom.py`（align チャネル=cid_align の実装）、`cid_full_vec`/`atom_centroids`/`robust_z`（既存資産）
