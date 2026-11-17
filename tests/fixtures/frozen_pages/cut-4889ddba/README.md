# Cut `4889ddba`: every committed page at main `4889ddba632f34b0479fdb4e6e6e1b32c095cb10`

Each folder `<T>/` holds `data/dossiers/<T>/dossier.json` and `dossier.md` as committed at main
`4889ddba` (#1092, the coverage roster, 2026-11-17), byte for byte. They are the same git blobs, so
the cut added 0 objects to the repository. The cut was taken by `git cat-file blob` of each page
file's blob at that commit, then checked by `git hash-object`. It was not hand-rolled and not
re-serialized.

It carries all 26 pages the roster covered at the cut (11 active, 15 watch). It is the one frozen
copy of each page for the pins moved off the living pages by the W27 follow-up (STATE row 41 (a)).
Tests read it through `tests/frozen_support.py`. Which pins read a copy is derived
(`grep 'frozen_doc("T")'`), never listed here.

`tests/test_frozen_pages_are_cuts.py` holds this table to the copies (each blob below is the
copy's, and so the committed page's at the cut), and each copy to `git show 4889ddba:…`. Never
edit a copy. A page that moves on main gets a new cut.

| page | roster status at the cut | assembled | reference date | `dossier.json` blob | `dossier.md` blob |
|---|---|---|---|---|---|
| AMZN | watch | 2026-11-03 | 2026-10-16 | `9fbae9aa72ea73aba1e2c0f5545f6c2b04379cfc` | `8d205c1773d9442ac0aab4131529f570187f16e9` |
| BRBR | active | 2026-10-26 | 2026-10-16 | `0f2c2fbebba7bc0b91ecf173469319cc7439e157` | `f20df403713a6328e16cf2d265752c657fbc7098` |
| BURL | watch | 2026-10-26 | 2026-10-16 | `81a2c4d1ce56eade5bc8ee0ffb13fa4a80a9fa5b` | `45abb7a84cbf578f9b39b5094e791d3e2eda0680` |
| CNXC | watch | 2026-10-29 | 2026-10-16 | `f376e88ccae2ec9788f161dba9828d9c8a4ee272` | `b2ce9de488888f87eb5ec2a37521e1c561d7c1b0` |
| EPAM | active | 2026-11-14 | 2026-10-16 | `e7980ab2ced8b5ea0a6f6852b7104004f4bc693e` | `ac0ebfda21c49c09df0912df0ece2bef867e6c00` |
| FUBO | watch | 2026-08-18 | 2026-08-14 | `f5df4b5c595aa990e323d529d34c488e3fb6f50b` | `1aac92dad4a6cf7c8c6446b712fe77c0d6fe9e0a` |
| GOOGL | active | 2026-11-14 | 2026-10-16 | `c6218ffcbf38e51bd73e60246f95cbbcb914e5bb` | `0780432aa821ac05333f16ddb0c56ec90e07ad3d` |
| IT | active | 2026-11-14 | 2026-10-16 | `13e120eba62c1c3cc0621bb8ff2e9e0f1c378d34` | `d7a81f277a348f004d7ef0a18f10cb871cf855bc` |
| LLY | active | 2026-11-14 | 2026-10-16 | `5c6f07634f963d87a3ce5cf9274eda01ebae594a` | `7919144b5e3c2b8de81c55130ac4e39b8a44ed82` |
| MCK | watch | 2026-11-05 | 2026-10-16 | `7960bc0965cd03916ac446b6df7ab3560e0a7e57` | `4ed6695e97a0c5904ee79fb5998cdee2875b1afb` |
| NCNO | active | 2026-11-14 | 2026-10-16 | `c338a91b670c0969cd107d7bad4ee76864fec64e` | `81415b6e13e650e2d094772ea0e3941321234d61` |
| NFLX | watch | 2026-11-05 | 2026-10-16 | `88717b23ae4ec687d0ea43c1c68837f1914e0d8c` | `1ae4e54409e1e1f651392c95ce4c70ea53ed0077` |
| NKE | watch | 2026-10-29 | 2026-10-16 | `bd836c13183a5e97aeb45e1672c090cb60bb7db4` | `1a2cc63397422d63ea2477141b6f251ae26253e3` |
| ORKA | watch | 2026-10-26 | 2026-10-16 | `73e5ff1ec899c3710866023148f20cda5f6e6cfc` | `b65c7276047361b720f7b904c012ae37138b7f40` |
| PARR | watch | 2026-10-26 | 2026-10-16 | `2f547655508fe5f627653ffd33e5de746b499417` | `75464421049cf703540383ed9743f7bc1cdc4990` |
| ROST | watch | 2026-10-29 | 2026-10-16 | `231033094b4a2adce66c48612fc2ac92c4651eb8` | `20ec46f663f2eb29275b79a4a39951dd164caf5b` |
| SMPL | active | 2026-11-14 | 2026-10-16 | `f8c2a9f74d62c90378ea4579c99eacc67d0e18ea` | `02d657699d0bb52f99f1c35db0da2b0d42175ee3` |
| TECX | watch | 2026-11-10 | 2026-10-16 | `c8f732c6ea7a6d1f7d6ffb39b6746e131af2e4de` | `680b6891c8939b9f7d9d7c302856583985d1b3ac` |
| TGT | watch | 2026-10-26 | 2026-10-16 | `42036f2f68916350650d6a81b66e8941c51aa99a` | `aa40b9543c3047170a179f87e1923cc9b7077512` |
| TJX | active | 2026-11-14 | 2026-10-16 | `0766aab514c2e00a2b07735552b85402742043d3` | `0445aac3bd681ef122676bcd37c83e71060edd42` |
| UBER | watch | 2026-11-09 | 2026-10-16 | `177f7022168addc6ea7a64a6528cae0a50ffc9b5` | `ebb7396db7e232b3fd63ab14ef37f39c1b1f1c8f` |
| V | watch | 2026-11-09 | 2026-10-16 | `327c45efadb723d592931f10f2c98c31ef422bc0` | `1b2fb35988be277b5c9e08e9c1af3fb10039c32c` |
| VITL | active | 2026-11-14 | 2026-10-16 | `f078a763768b0065bf5576be94370be3e9d2d417` | `5037a4594516a1fad9e16b895aacf22449f48c24` |
| VRRM | active | 2026-11-09 | 2026-10-16 | `5c73313de425997026ad0d7875f106975b8ebba4` | `5db8351ad10de802c457134b5602b0bd50695f5f` |
| WERN | active | 2026-11-14 | 2026-10-16 | `b66e67cfc17addca7957b42efc692480187bbd85` | `9b05cc469824c9e9874849dbe7435c45d12b50e3` |
| WLK | watch | 2026-11-09 | 2026-10-16 | `96848ed4fd280c7f9223a738df3439dac14e3b86` | `125d2b470715c3cf710927a1fc113f67bd5725a4` |
