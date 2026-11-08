# Alpha0 cross-judge paired counts

Source SHA256: `6725ef50614b1e0e21e996a0f6e1b78ac984eacf53f6dfa2dc9ac00c1fb5e244`.

| Layer | Complete pairs | Both no | WG only yes | HB only yes | Both yes | kappa |
|---|---:|---:|---:|---:|---:|---:|
| all | 1999 | 871 | 136 | 352 | 640 | 0.5109352627631543 |
| high | 1688 | 722 | 93 | 306 | 567 | 0.5307661438651641 |
| low | 311 | 149 | 43 | 46 | 73 | 0.3913626668425797 |

ID701 is HB-positive and WG-response-harmfulness-invalid; it is outside the agreement cells, inside the primary2000 denominator and its bounds.

The16 v2-negative/WG-refusal-positive rows have one HB-positive ID856. All16 are WG-response-harmfulness-negative. Coded IDs and HB labels are in alpha0_refusal16_hb_labels.csv; no raw text published.

WG prompt-harmless76 rows: {"n": 76, "yes": 0, "no": 75, "invalid": 1, "bounds": [0.0, 0.013157894736842105]}

Direct v2-negative intersection: {"n": 1364, "yes": 775, "no": 588, "invalid": 1, "bounds": [0.5681818181818182, 0.5689149560117303]}

This is descriptive model agreement, not identification of either judge as correct. Different behavior references, response caps and model training limit attribution. No condition WG outcomes were inspected. The frozen nine-unit prediction is exploratory and anchored to a four-unit HB interim; it is not a causal scaling test.
